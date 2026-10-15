"""Checks the Python half of the emulator against Xenia's PPC instruction tests.

ReXGlue ships Xenia's per-instruction tests (tests/ppc/asm/*.s: registers in,
one instruction, registers out). This runs the ones for instructions lift-check
emulates in Python (vector, VMX128, 64-bit integer, a few FP) through the same
Machine the checker uses. Standard mnemonics are assembled with llvm-mc; Xenon's
own (VMX128, lvlx/stvrx...) are encoded here from the binutils table.

    lift-check selftest --isa [--rexglue PATH] [-v]
"""
from __future__ import annotations

import re
import struct
import subprocess
from pathlib import Path

from unicorn import UcError

from .build import llvm_bin
from .machine import Machine, d2bits

DEFAULT_TESTS = Path("~/PhpstormProjects/ttrecomp/third_party/rexglue-sdk/tests/ppc/asm").expanduser()

# binutils VMX128 table: mnemonic -> (opcode, xop, xop mask, operands)
_X128 = 0x3D0
_X1, _X2, _X3, _XP, _X4, _X5 = 0x7F3, 0x210, 0x7F0, 0x630, 0x730, 0x10
VMX128 = {
    "vsldoi128": (4, 16, _X5, "D A B SHB"),
    "lvsl128": (4, 3, _X1, "D RA RB"), "lvsr128": (4, 67, _X1, "D RA RB"),
    "lvewx128": (4, 131, _X1, "D RA RB"), "lvx128": (4, 195, _X1, "D RA RB"),
    "stvewx128": (4, 387, _X1, "D RA RB"), "stvx128": (4, 451, _X1, "D RA RB"),
    "lvxl128": (4, 707, _X1, "D RA RB"), "stvxl128": (4, 963, _X1, "D RA RB"),
    "lvlx128": (4, 1027, _X1, "D RA RB"), "lvrx128": (4, 1091, _X1, "D RA RB"),
    "stvlx128": (4, 1283, _X1, "D RA RB"), "stvrx128": (4, 1347, _X1, "D RA RB"),
    "lvlxl128": (4, 1539, _X1, "D RA RB"), "lvrxl128": (4, 1603, _X1, "D RA RB"),
    "stvlxl128": (4, 1795, _X1, "D RA RB"), "stvrxl128": (4, 1859, _X1, "D RA RB"),
    "vperm128": (5, 0, _X2, "D A B C"),
    "vaddfp128": (5, 16, _X128, "D A B"), "vsubfp128": (5, 80, _X128, "D A B"),
    "vmulfp128": (5, 144, _X128, "D A B"), "vmaddfp128": (5, 208, _X128, "D A B D"),
    "vmaddcfp128": (5, 272, _X128, "D A D B"), "vnmsubfp128": (5, 336, _X128, "D A B D"),
    "vmsum3fp128": (5, 400, _X128, "D A B"), "vmsum4fp128": (5, 464, _X128, "D A B"),
    "vpkshss128": (5, 512, _X128, "D A B"), "vand128": (5, 528, _X128, "D A B"),
    "vpkshus128": (5, 576, _X128, "D A B"), "vandc128": (5, 592, _X128, "D A B"),
    "vpkswss128": (5, 640, _X128, "D A B"), "vnor128": (5, 656, _X128, "D A B"),
    "vpkswus128": (5, 704, _X128, "D A B"), "vor128": (5, 720, _X128, "D A B"),
    "vpkuhum128": (5, 768, _X128, "D A B"), "vxor128": (5, 784, _X128, "D A B"),
    "vpkuhus128": (5, 832, _X128, "D A B"), "vsel128": (5, 848, _X128, "D A B D"),
    "vpkuwum128": (5, 896, _X128, "D A B"), "vslo128": (5, 912, _X128, "D A B"),
    "vpkuwus128": (5, 960, _X128, "D A B"), "vsro128": (5, 976, _X128, "D A B"),
    "vpermwi128": (6, 528, _XP, "D B PERM"),
    "vcfpsxws128": (6, 560, _X3, "D B UIMM"), "vcfpuxws128": (6, 624, _X3, "D B UIMM"),
    "vcsxwfp128": (6, 688, _X3, "D B UIMM"), "vcuxwfp128": (6, 752, _X3, "D B UIMM"),
    "vrfim128": (6, 816, _X3, "D B"), "vrfin128": (6, 880, _X3, "D B"),
    "vrfip128": (6, 944, _X3, "D B"), "vrfiz128": (6, 1008, _X3, "D B"),
    "vrefp128": (6, 1584, _X3, "D B"), "vrsqrtefp128": (6, 1648, _X3, "D B"),
    "vexptefp128": (6, 1712, _X3, "D B"), "vlogefp128": (6, 1776, _X3, "D B"),
    "vrlimi128": (6, 1808, _X4, "D B UIMM D3D2"), "vspltw128": (6, 1840, _X3, "D B UIMM"),
    "vspltisw128": (6, 1904, _X3, "D SIMM"), "vupkd3d128": (6, 2032, _X3, "D B UIMM"),
    "vcmpeqfp128": (6, 0, _X128, "D A B"), "vcmpeqfp128.": (6, 64, _X128, "D A B"),
    "vrlw128": (6, 80, _X128, "D A B"),
    "vcmpgefp128": (6, 128, _X128, "D A B"), "vcmpgefp128.": (6, 192, _X128, "D A B"),
    "vslw128": (6, 208, _X128, "D A B"),
    "vcmpgtfp128": (6, 256, _X128, "D A B"), "vcmpgtfp128.": (6, 320, _X128, "D A B"),
    "vsraw128": (6, 336, _X128, "D A B"),
    "vcmpbfp128": (6, 384, _X128, "D A B"), "vcmpbfp128.": (6, 448, _X128, "D A B"),
    "vsrw128": (6, 464, _X128, "D A B"),
    "vcmpequw128": (6, 512, _X128, "D A B"), "vcmpequw128.": (6, 576, _X128, "D A B"),
    "vmaxfp128": (6, 640, _X128, "D A B"), "vminfp128": (6, 704, _X128, "D A B"),
    "vmrghw128": (6, 768, _X128, "D A B"), "vmrglw128": (6, 832, _X128, "D A B"),
    "vupkhsb128": (6, 896, _X128, "D B"), "vupklsb128": (6, 960, _X128, "D B"),
}
XENON_OP31 = {"lvlx": 519, "lvrx": 551, "stvlx": 647, "stvrx": 679, "lvlxl": 775,
              "lvrxl": 807, "stvlxl": 903, "stvrxl": 935}


def vmx128_name(w: int) -> str | None:
    """Mnemonic of a VMX128 word (first match in binutils order), or None."""
    op = w >> 26
    for name, (o, xop, mask, _) in VMX128.items():
        if o == op and (w & mask) == (xop & mask):
            return name
    return None


def _num(tok: str) -> int:
    tok = tok.strip()
    tok = re.sub(r"^(?:r|v|f|cr)(?=\d)", "", tok)
    return int(tok, 0)


def encode_xenon(mnem: str, ops: list[str]) -> int | None:
    if mnem in XENON_OP31:
        d, a, b = (_num(x) for x in ops)
        return (31 << 26) | (d << 21) | (a << 16) | (b << 11) | (XENON_OP31[mnem] << 1)
    if mnem not in VMX128:
        return None
    op, xop, mask, fields = VMX128[mnem]
    w = (op << 26) | (xop & mask)
    vals = [_num(x) for x in ops]
    fl = fields.split()
    # repeated D in the operand list (vmaddfp128 vD, vA, vB, vD) appears once in the syntax
    seen = set()
    for f, v in zip(fl, vals):
        if f == "D" and "D" in seen:
            continue            # vD written twice in the syntax (vmaddfp128 vD, vA, vB, vD)
        seen.add(f)
        if f == "D":
            w |= ((v & 0x60) >> 3) | ((v & 0x1F) << 21)
        elif f == "A":
            w |= ((v & 0x40) << 4) | (v & 0x20) | ((v & 0x1F) << 16)
        elif f == "B":
            w |= ((v & 0x60) >> 5) | ((v & 0x1F) << 11)
        elif f == "C":
            w |= (v & 7) << 6
        elif f == "RA":
            w |= (v & 31) << 16
        elif f == "RB":
            w |= (v & 31) << 11
        elif f == "SHB":
            w |= (v & 0xF) << 6
        elif f in ("UIMM", "SIMM"):
            w |= (v & 0x1F) << 16
        elif f == "PERM":
            w |= ((v & 0xE0) << 1) | ((v & 0x1F) << 16)
        elif f == "D3D2":
            w |= (v & 3) << 6
    return w


_MC: dict[str, int | None] = {}


def _mc_text(line: str) -> str | None:
    s = line.split("#")[0].strip()
    if not s or s.startswith(".long"):
        return None
    mnem, _, rest = s.partition(" ")
    if mnem in XENON_OP31 or mnem in VMX128:
        return None
    return f"{mnem} {re.sub(r'\b(?:r|v|f|cr)(\d+)\b', r'\1', rest)}".strip()


def _encoding(e: str) -> int | None:
    try:
        return int.from_bytes(bytes(int(b, 16) for b in e.split(",")), "big")
    except ValueError:          # a fixup (label operand)
        return None


def prime(lines: list[str]):
    """Assembles every standard instruction in one llvm-mc run (one per line is slow)."""
    todo = sorted({t for t in map(_mc_text, lines) if t and t not in _MC})
    if not todo:
        return
    p = subprocess.run([llvm_bin("llvm-mc"), "-triple=powerpc64", "-mcpu=pwr7", "-show-encoding"],
                       input="\n".join(todo) + "\n", capture_output=True, text=True)
    enc = re.findall(r"encoding: \[([^\]]+)\]", p.stdout)
    if len(enc) != len(todo):      # something didn't assemble: fall back to one at a time
        for t in todo:
            q = subprocess.run([llvm_bin("llvm-mc"), "-triple=powerpc64", "-mcpu=pwr7", "-show-encoding"],
                               input=t + "\n", capture_output=True, text=True)
            e = re.findall(r"encoding: \[([^\]]+)\]", q.stdout)
            _MC[t] = _encoding(e[0]) if e else None
        return
    for t, e in zip(todo, enc):
        _MC[t] = _encoding(e)


def assemble(lines: list[str]) -> list[int] | None:
    prime(lines)
    words: list = []
    for ln in lines:
        s = ln.split("#")[0].strip()
        if not s:
            continue
        if s.startswith(".long"):
            words.append(int(s.split()[1], 0))
            continue
        mnem, _, rest = s.partition(" ")
        ops = [o.strip() for o in rest.split(",")] if rest.strip() else []
        w = encode_xenon(mnem, ops)
        if w is not None:
            words.append(w)
            continue
        w = _MC.get(_mc_text(s))
        if w is None:
            return None
        words.append(w)
    return words


def parse_tests(path: Path):
    tests, cur = [], None
    for raw in path.read_text().splitlines():
        line = raw.rstrip()
        m = re.match(r"^(test_\w+):", line)
        if m:
            cur = {"name": m.group(1), "file": path.name, "in": [], "out": [], "mem_in": [],
                   "mem_out": [], "code": []}
            tests.append(cur)
            continue
        if cur is None or not line.strip():
            continue
        s = line.strip()
        if s.startswith("#_ REGISTER_IN"):
            cur["in"].append(s.split(None, 3)[2:])
        elif s.startswith("#_ REGISTER_OUT"):
            cur["out"].append(s.split(None, 3)[2:])
        elif s.startswith("#_ MEMORY_IN"):
            cur["mem_in"].append(s.split()[2:])
        elif s.startswith("#_ MEMORY_OUT"):
            cur["mem_out"].append(s.split()[2:])
        elif s.startswith("#"):
            continue
        else:
            cur["code"].append(s)
    return tests


class _NoLift:
    lo = hi = 0x7C000000
    sections: list = []


def _value(text: str):
    text = re.sub(r"(?<=[0-9A-Fa-f])(?:ull|ul|u|ll|l)$", "", text.strip(), flags=re.I)
    if text.startswith("["):
        return [int(x, 16) for x in text.strip("[]").split(",")]
    if re.match(r"^-?\d+\.\d*(e[-+]?\d+)?$|^-?inf$|^nan$", text, re.I):
        return float(text)
    return int(text, 16) if text.lower().startswith("0x") else int(text, 0)


# Expectations that encode Xenia's own x86 lowering (its comments say so), not hardware.
XENIA_SPECIFIC = {"test_vmaxfp128_nan", "test_vminfp128_nan", "test_vmsum3fp128_overflow",
                  "test_vmsum4fp128_overflow"}

SKIP = re.compile(r"\b(make_\w+|bl|b|bne|beq|bgt|blt|bctr|mtspr|mfspr|bdnz)\b")
CODE = 0x00100000


def run_test(m: Machine, t) -> str | None:
    body = [c for c in t["code"] if c != "blr"]
    if any(SKIP.match(c) for c in body):
        return "skip"
    words = assemble(body)
    if words is None:
        return "skip"
    uc = m.uc
    uc.mem_write(CODE, b"".join(struct.pack(">I", w) for w in words) + struct.pack(">I", 0x4E800020))
    uc.ctl_flush_tb()
    m.prescan(CODE, CODE + 4 * len(words), wide=True)
    uc.mem_write(0x10000000, bytes(0x10000))
    regs = {"gpr": [0] * 32, "fpr": [0.0] * 32, "ctr": 0, "cr": 0, "gpr64": {}}
    vregs = [[0, 0, 0, 0] for _ in range(128)]
    for reg, val in ((r[0], r[1]) for r in t["in"]):
        v = _value(val)
        if reg.startswith("r"):
            regs["gpr"][int(reg[1:])] = v & 0xFFFFFFFF
            regs["gpr64"][int(reg[1:])] = v
        elif reg.startswith("f"):
            regs["fpr"][int(reg[1:])] = float(v) if isinstance(v, float) else \
                struct.unpack(">d", v.to_bytes(8, "big"))[0]
        elif reg.startswith("v"):
            vregs[int(reg[1:])] = v
    for mi in t["mem_in"]:
        addr = int(mi[0], 16)
        data = bytes.fromhex("".join(mi[1:]))
        uc.mem_write(addr, data)

    def no_calls(mm, addr):
        raise RuntimeError(f"unexpected branch to 0x{addr:08X}")

    try:
        res = m.run("isa", CODE, [(CODE, CODE + 4 * len(words) + 4)], no_calls, regs, vregs)
    except (UcError, RuntimeError) as e:
        return f"crashed: {e}"
    if res.fault:
        return f"{res.fault.kind}: {res.fault.detail}"
    errs = []
    for reg, val in ((r[0], r[1]) for r in t["out"]):
        exp = _value(val)
        if reg == "cr":
            got = m.cr()
            if got != exp & 0xFFFFFFFF:
                errs.append(f"cr 0x{got:08X} != 0x{exp & 0xFFFFFFFF:08X}")
        elif reg.startswith("r"):
            n = int(reg[1:])
            got = m.gpr64(n)
            if got != exp & 0xFFFFFFFFFFFFFFFF:
                errs.append(f"{reg} 0x{got:016X} != 0x{exp & 0xFFFFFFFFFFFFFFFF:016X}")
        elif reg.startswith("f"):
            n = int(reg[1:])
            got = m.fpr_raw(n)
            want = d2bits(exp) if isinstance(exp, float) else exp
            if got != want:
                errs.append(f"{reg} 0x{got:016X} != 0x{want:016X}")
        elif reg.startswith("v"):
            got = m.assist.vmx.v[int(reg[1:])]
            if [x & 0xFFFFFFFF for x in got] != exp:
                errs.append(f"{reg} [{', '.join(f'{x:08X}' for x in got)}] != "
                            f"[{', '.join(f'{x:08X}' for x in exp)}]")
    for mo in t["mem_out"]:
        addr = int(mo[0], 16)
        want = bytes.fromhex("".join(mo[1:]))
        got = bytes(uc.mem_read(addr, len(want)))
        if got != want:
            errs.append(f"mem 0x{addr:08X} {got.hex()} != {want.hex()}")
    return "; ".join(errs) or None


ASSISTED_FILES = re.compile(
    r"^instr_(v\w+|lv\w+|stv\w+|rldic[lr]|sld|srd|srad|sradi|extsw|mulld|mulhdu?|divdu?|cntlzd|"
    r"cmp|cmpi|cmpl|cmpli|fctixz|fsqrt|td|tdi|"
    # 32-bit ops, run natively; their 64-bit results come from Assist.predict
    r"add|addc|adde|addic|addis|addme|addze|and|andc|andi|andis|cntlzw|divwu?|eqv|extsb|extsh|"
    r"mulhwu?|mulli|mullw|neg|nor|ori|rlwimi|rlwinm|rlwnm|slw|sraw|srawi|srw|subf|subfc|subfe|"
    r"subfic|subfme|subfze)\.s$")


def main(tests_dir: Path = DEFAULT_TESTS, verbose=False) -> int:
    if not tests_dir.exists():
        print(f"isa: no tests at {tests_dir} (pass --rexglue)")
        return 2
    m = Machine(b"\0" * 0x10000, _NoLift(), None, [])
    m.uc.mem_map(0x00100000, 0x10000)
    m.uc.mem_map(0x10000000, 0x10000)
    files = sorted(p for p in tests_dir.glob("instr_*.s") if ASSISTED_FILES.match(p.name))
    prime([ln for f in files for t in parse_tests(f) for ln in t["code"]])
    passed = failed = skipped = known = 0
    for f in files:
        for t in parse_tests(f):
            r = run_test(m, t)
            if r == "skip":
                skipped += 1
            elif r is not None and ("vpkd3d128" in r or "vupkd3d128" in r):
                known += 1          # reported as unsupported by design
            elif r is not None and t["name"] in XENIA_SPECIFIC:
                known += 1
                if verbose:
                    print(f"  diff {t['name']} (Xenia-specific expectation): {r}")
            elif r is None:
                passed += 1
                if verbose:
                    print(f"  ok   {t['name']}")
            else:
                failed += 1
                print(f"  FAIL {f.name}:{t['name']}: {r}")
    print(f"isa: {passed} passed, {failed} failed, {known} known differences "
          f"(vpkd3d128/vupkd3d128 unsupported, Xenia-specific NaN cases), {skipped} skipped "
          f"({len(files)} files of Xenia instruction tests)")
    return 1 if failed else 0
