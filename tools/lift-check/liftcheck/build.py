"""Cross-compiles a lifted TU for 32-bit big-endian PowerPC and links it next to the image.

The TU is compiled whole, freestanding, against `shim/` (a tiny libc/libstdc++
stand-in) and the repo's own include dirs, with `-fno-inline` so every call the
lift makes stays a call. The linker keeps only what the function under test
reaches (`--gc-sections -e <symbol>`); each symbol it can't find is resolved to
an original address through the symbol map or a `// @ 0x...` marker and passed
with `--defsym`, so a call to `game_D1C0` jumps straight to 0x820DD1C0.
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

from .dwarf import Dwarf, Signature
from .elf import Section, load_sections
from .symbols import Symbols, base_name

LIFT_BASE = 0x82800000
TOOL_DIR = Path(__file__).resolve().parent.parent


def llvm_bin(name: str) -> str:
    d = os.environ.get("LIFTCHECK_LLVM", "/opt/homebrew/opt/llvm/bin")
    p = Path(d) / name
    if p.exists():
        return str(p)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit(f"lift-check: can't find {name} (set LIFTCHECK_LLVM to an LLVM bin dir)")


def ld_lld() -> str:
    for cand in (os.environ.get("LIFTCHECK_LLD"), "/opt/homebrew/opt/lld/bin/ld.lld",
                 "/opt/homebrew/bin/ld.lld", shutil.which("ld.lld")):
        if cand and Path(cand).exists():
            return cand
    raise SystemExit("lift-check: can't find ld.lld (brew install lld, or set LIFTCHECK_LLD)")


class BuildError(Exception):
    pass


@dataclass
class LiftFunc:
    addr: int
    size: int
    mangled: str
    demangled: str


@dataclass
class Lift:
    elf: Path
    obj: Path
    sections: list[Section]
    target: LiftFunc
    funcs: dict[int, LiftFunc]                 # every live function in the lift's .text
    call_map: dict[int, int]                   # lift function -> original address it stands for
    externs: dict[str, int]                    # undefined symbol -> original address
    signatures: dict[int, Signature]           # original address -> lift's declaration of it
    target_sig: Signature | None
    lo: int
    hi: int
    data_syms: dict[int, tuple[str, int]] = field(default_factory=dict)   # lift data addr -> (name, size)

    def symbolize(self, addr: int) -> str | None:
        for a, (name, size) in self.data_syms.items():
            if a <= addr < a + max(size, 1):
                return f"{name}+0x{addr - a:X}" if addr != a else name
        for f in self.funcs.values():
            if f.addr <= addr < f.addr + f.size:
                return f"{f.demangled}+0x{addr - f.addr:X}"
        return None


_LINKER_SCRIPT = """
SECTIONS {
  . = 0x%X;
  .text : { *(.text .text.*) }
  . = ALIGN(16);
  .rodata : { *(.rodata .rodata.* .data.rel.ro .data.rel.ro.*) }
  . = ALIGN(16);
  .data : { *(.data .data.* .sdata .sdata.* .got2 .got) }
  . = ALIGN(16);
  .bss : { *(.bss .bss.* .sbss .sbss.* COMMON) }
  /DISCARD/ : { *(.comment) *(.note*) *(.eh_frame*) }
}
"""


def _run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    return p


def _demangle(names: list[str]) -> dict[str, str]:
    if not names:
        return {}
    p = _run([llvm_bin("llvm-cxxfilt")], input="\n".join(names) + "\n")
    out = p.stdout.splitlines()
    return dict(zip(names, out)) if len(out) == len(names) else {n: n for n in names}


def _nm(path: Path) -> list[tuple[int, int, str, str]]:
    p = _run([llvm_bin("llvm-nm"), "-S", "--defined-only", "--no-sort", str(path)])
    rows = []
    for line in p.stdout.splitlines():
        parts = line.split(None, 3)
        if len(parts) == 4:
            rows.append((int(parts[0], 16), int(parts[1], 16), parts[2], parts[3]))
        elif len(parts) == 3 and len(parts[1]) == 1:
            rows.append((int(parts[0], 16), 0, parts[1], parts[2]))
    return rows


_LINKAGE = re.compile(r"^(private|internal|linkonce_odr|linkonce|weak_odr|weak|available_externally|"
                      r"external|common|extern_weak)\s+")


def _declare_functions(ir: str, names: set[str], keep: str) -> str:
    """Turns the definitions of `names` into declarations, lets the rest inline, and
    gives `keep` (the function under test) external linkage so -O2 can't drop it."""
    out, lines, k = [], ir.split("\n"), 0
    while k < len(lines):
        line = lines[k]
        m = re.match(r'^define ([^@]*)@("[^"]+"|[\w.$]+)\(', line)
        if m and m.group(2).strip('"') == keep:
            prefix = m.group(1)
            while _LINKAGE.match(prefix):
                prefix = prefix[_LINKAGE.match(prefix).end():]
            line = "define " + prefix + line[m.start(2) - 1:]
            line = re.sub(r"\s+comdat(\([^)]*\))?", "", line)
            out.append(line)
            k += 1
            continue
        if m and m.group(2).strip('"') in names:
            prefix = m.group(1)
            while True:
                lm = _LINKAGE.match(prefix)
                if not lm:
                    break
                prefix = prefix[lm.end():]
            # cut at the parenthesis closing the parameter list
            start = m.end() - 1
            depth, end = 0, start
            for j in range(start, len(line)):
                if line[j] == "(":
                    depth += 1
                elif line[j] == ")":
                    depth -= 1
                    if depth == 0:
                        end = j + 1
                        break
            attrs = re.findall(r"#\d+", line[end:])
            out.append(f"declare {prefix}@{m.group(2)}{line[start:end]} {' '.join(attrs)}".rstrip())
            while k < len(lines) and lines[k] != "}":
                k += 1
            k += 1
            continue
        if line.startswith("attributes #"):
            line = line.replace(" noinline", "").replace("{ noinline", "{")
        out.append(line)
        k += 1
    return "\n".join(out)


def compile_flags(repo: Path, source: Path, opt: str) -> list[str]:
    is_c = source.suffix == ".c"
    flags = [
        "--target=powerpc-unknown-elf", "-mcpu=970", "-mno-altivec",
        "-std=c11" if is_c else "-std=c++17", opt, "-g",
        "-ffreestanding", "-fno-strict-aliasing", "-fwrapv", "-fno-pic",
        "-ffunction-sections", "-fdata-sections", "-fno-common", "-nostdlibinc",
        "-isystem", str(TOOL_DIR / "shim"),
        "-I", str(repo / "include"), "-I", str(repo / "src"),
        "-iquote", str(source.parent), "-w",
    ]
    if not is_c:
        flags += ["-nostdinc++", "-fno-exceptions", "-fno-rtti", "-fno-threadsafe-statics",
                  "-fno-use-cxa-atexit", "-Xclang", "-mno-constructor-aliases"]
    return flags


def build_lift(repo: Path, syms: Symbols, source: Path, function: str, *, orig_addr: int,
               workdir: Path, opt: str = "-O2", patches=(), extra_flags=(),
               externs_override: dict | None = None) -> Lift:
    clang = llvm_bin("clang")
    source = source.resolve()
    key = hashlib.sha1(repr((str(source), function, opt, patches, extra_flags)).encode()).hexdigest()[:10]
    out = workdir / f"{source.stem}-{key}"
    out.mkdir(parents=True, exist_ok=True)

    tu = source
    if patches:
        text = source.read_text()
        for old, new in patches:
            if old not in text:
                raise BuildError(f"patch text not found in {source.name}: {old!r}")
            text = text.replace(old, new, 1)
        tu = out / source.name
        tu.write_text(text)

    # 0. in the background: an ordinary -O1 -g object, only for its debug info
    #    (signatures of every callee and the struct layouts the specs name)
    dwarf_obj = out / "dwarf.o"
    dwarf_job = subprocess.Popen([clang, *compile_flags(repo, source, "-O1"), *extra_flags, "-c", str(tu),
                                  "-o", str(dwarf_obj)], stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)

    # 1. IR straight from the front end, before any pass has looked across functions
    ll = out / "lift.ll"
    cmd = [clang, *compile_flags(repo, source, "-O1"), "-Xclang", "-disable-llvm-passes",
           *extra_flags, "-S", "-emit-llvm", str(tu), "-o", str(ll)]
    p = _run(cmd)
    if p.returncode != 0:
        raise BuildError("compile failed:\n" + "\n".join(p.stderr.splitlines()[:25]))
    ir = ll.read_text()
    defined = re.findall(r'^define [^@]*@("[^"]+"|[\w.$]+)\(', ir, re.M)
    names = [d.strip('"') for d in defined]
    dem = _demangle(names)
    target_sym = None
    for name in names:
        d = dem.get(name, name)
        if name == function or d == function or base_name(d) == function:
            target_sym = name
            break
    if target_sym is None:
        cands = [dem.get(n, n) for n in names if function.split("::")[-1] in dem.get(n, n)]
        raise BuildError(f"no function '{function}' in {source.name}"
                         + (f"; close: {', '.join(cands[:6])}" if cands else ""))

    # 2. every other function that stands for an original one becomes a declaration,
    #    so the lift calls the original address and the optimiser can't peek inside
    override = externs_override or {}
    stubbed = set()
    for name in names:
        if name == target_sym:
            continue
        d = dem.get(name, name)
        a = override.get(name, override.get(d, override.get(base_name(d))))
        if a is None:
            a = syms.resolve(name, d)
        if a is not None:
            stubbed.add(name)
    ir = _declare_functions(ir, stubbed, keep=target_sym)
    ll2 = out / "lift.opaque.ll"
    ll2.write_text(ir)

    # 3. optimise and generate code
    obj = out / "lift.o"
    p = _run([clang, "--target=powerpc-unknown-elf", "-mcpu=970", "-mno-altivec", opt, "-fno-pic",
              "-ffunction-sections", "-fdata-sections", "-w", "-c", str(ll2), "-o", str(obj)])
    if p.returncode != 0:
        raise BuildError("codegen failed:\n" + "\n".join(p.stderr.splitlines()[:25]))

    script = out / "link.ld"
    script.write_text(_LINKER_SCRIPT % LIFT_BASE)
    elf = out / "lift.elf"
    base = [ld_lld(), "-m", "elf32ppc", "-T", str(script), "--gc-sections", "--no-demangle",
            "-e", target_sym, "-o", str(elf), str(obj)]
    p = _run(base + ["--warn-unresolved-symbols"])
    undefined = sorted(set(re.findall(r"undefined symbol: (\S+)", p.stderr)))
    if p.returncode != 0 and not undefined:
        raise BuildError("link failed:\n" + p.stderr[:2000])

    udem = _demangle(undefined)
    externs, missing = {}, []
    for u in undefined:
        d = udem.get(u, u)
        a = override.get(u, override.get(d, override.get(base_name(d))))
        if a is None:
            a = syms.resolve(u, d)
        if a is None:
            missing.append(d)
        else:
            externs[u] = a
    if missing:
        raise BuildError("can't map these to original addresses (add them to EXTERNS in the spec,\n"
                         "or give them a `// @ 0x...` marker):\n  " + "\n  ".join(missing))

    p = _run(base + [f"--defsym={u}=0x{a:X}" for u, a in externs.items()])
    if p.returncode != 0:
        raise BuildError("link failed:\n" + p.stderr[:2000])

    sections = load_sections(str(elf))
    lo = min(s.addr for s in sections)
    hi = max(s.addr + s.size for s in sections)

    frows = _nm(elf)
    fdem = _demangle([r[3] for r in frows])
    funcs, data_syms = {}, {}
    target = None
    for addr, size, typ, name in frows:
        d = fdem.get(name, name)
        if typ.upper() in ("T", "W") and lo <= addr < hi:
            f = LiftFunc(addr, size, name, d)
            funcs[addr] = f
            if name == target_sym:
                target = f
        elif typ.upper() in ("D", "B", "R", "V") and lo <= addr < hi:
            data_syms[addr] = (d, size)
    if target is None:
        raise BuildError(f"{function} vanished at link time")

    call_map = {}
    for addr, f in funcs.items():
        if f is target or f.demangled.startswith("__LongThunk"):
            continue
        a = override.get(f.mangled, override.get(base_name(f.demangled)))
        if a is None:
            a = syms.resolve(f.mangled, f.demangled)
        if a is not None:
            call_map[addr] = a

    if dwarf_job.wait() != 0:
        raise BuildError("debug-info compile failed")
    dwarf = Dwarf(str(dwarf_obj), llvm_bin("llvm-dwarfdump"))
    signatures = {}
    for u, a in externs.items():
        s = dwarf.signature(u)
        if s:
            signatures[a] = s
    for la, a in call_map.items():
        s = dwarf.signature(funcs[la].mangled)
        if s:
            signatures[a] = s
    target_sig = dwarf.signature(target_sym)
    resolved = syms.resolve(target.mangled, target.demangled)
    if resolved is not None and resolved != orig_addr:
        print(f"lift-check: note: {target.demangled} is marked @ 0x{resolved:08X}, "
              f"spec says 0x{orig_addr:08X}")
    return Lift(elf, dwarf_obj, sections, target, funcs, call_map, externs, signatures, target_sig,
                lo, hi, data_syms)
