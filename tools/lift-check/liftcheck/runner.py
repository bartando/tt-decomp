"""Runs a spec: builds the lift, then N trials of original vs lift, and compares."""
from __future__ import annotations

import importlib.util
import os
import random
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

from unicorn import ppc_const as _P

from .build import build_lift
from .dwarf import arg_registers
from .machine import (ARENA_BASE, FAKE_BASE, FAKE_SIZE, IMAGE_BASE, STACK_HI, STACK_LO,
                      STACK_TOP, TLS_BASE, CallRecord, Fault, Machine, Stop)
from .spec import MODELS, CallCtx, Policy, Trial, stub
from .symbols import Symbols

DEFAULT_IMAGE = "~/PhpstormProjects/ttrecomp/out/xexdump/default_82000000_00770000.bin"
NONVOLATILE_GPR = [1, 2, 13] + list(range(14, 32))
NONVOLATILE_FPR = list(range(14, 32))
M32 = 0xFFFFFFFF
_PC = _P.UC_PPC_REG_PC
_LR = _P.UC_PPC_REG_LR


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def load_spec(path: Path):
    spec = importlib.util.spec_from_file_location(f"liftcheck_spec_{path.stem}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for need in ("FUNCTION", "ADDRESS", "SOURCE", "inputs"):
        if not hasattr(mod, need):
            raise SystemExit(f"{path}: spec needs {need}")
    return mod


def f32_rounds(x: float) -> float:
    try:
        return struct.unpack(">f", struct.pack(">f", x))[0]
    except OverflowError:
        return x


class Divergence(Exception):
    def __init__(self, title, lines):
        super().__init__(title)
        self.title = title
        self.lines = lines


@dataclass
class Options:
    trials: int | None = None
    seed: int = 1
    ftol: float | None = None
    opt: str = "-O2"
    source: str | None = None
    patches: tuple = ()
    only: int | None = None
    verbose: bool = False
    quiet: bool = False
    workdir: Path | None = None


class Checker:
    def __init__(self, spec_path: Path, opts: Options):
        self.opts = opts
        self.repo = repo_root()
        self.spec = load_spec(spec_path)
        self.name = spec_path.stem
        self.syms = Symbols(self.repo)
        self.addr = self.spec.ADDRESS
        self.ftol = opts.ftol if opts.ftol is not None else getattr(self.spec, "FTOL", 0.0)
        self.trials = opts.trials if opts.trials is not None else getattr(self.spec, "TRIALS", 200)
        image_path = os.path.expanduser(os.environ.get("TT_IMAGE", DEFAULT_IMAGE))
        if not Path(image_path).exists():
            raise SystemExit(f"lift-check: game image not found at {image_path} (set TT_IMAGE)")
        self.image = Path(image_path).read_bytes()
        source = Path(opts.source) if opts.source else self.repo / self.spec.SOURCE
        workdir = opts.workdir or (Path(__file__).resolve().parent.parent / "build")
        self.lift = build_lift(self.repo, self.syms, source, self.spec.FUNCTION, orig_addr=self.addr,
                               workdir=workdir, opt=opts.opt, patches=tuple(opts.patches),
                               externs_override=getattr(self.spec, "EXTERNS", None))
        rng = self.syms.func_range(self.addr)
        if rng is None:
            raise SystemExit(f"lift-check: 0x{self.addr:08X} isn't a function in the symbol map")
        self.orig_range = rng
        self.machine = Machine(self.image, self.lift, self.syms, self.syms.helper_ranges())
        m = self.machine
        m.prescan(*rng)
        for extra in getattr(self.spec, "EXTRA_RANGES", ()):
            m.prescan(*extra)
        for lo, hi in self.syms.helper_ranges():
            m.prescan(lo, hi)
        m.prescan(self.lift.lo, self.lift.hi & ~3)
        mapped = set(self.lift.call_map)
        self.lift_home = []
        text_hi = max(f.addr + f.size for f in self.lift.funcs.values())
        cur = self.lift.lo
        for f in sorted(self.lift.funcs.values(), key=lambda f: f.addr):
            if f.addr in mapped:
                if cur < f.addr:
                    self.lift_home.append((cur, f.addr))
                cur = f.addr + f.size
        self.lift_home.append((cur, text_hi))
        self.policies: dict = {}
        self.fake_policies: dict = {}
        for key, pol in getattr(self.spec, "CALLS", {}).items():
            if isinstance(key, int):
                self.policies[key] = pol
            elif key in self.syms.by_name:
                self.policies[self.syms.by_name[key]] = pol
            else:
                a = self.syms.resolve(key, key)
                if a is not None:
                    self.policies[a] = pol
                else:
                    self.fake_policies[key] = pol
        self.disasm_cache: dict[int, str] = {}

    # ── one side ────────────────────────────────────────────────────────────
    def _policy(self, target: int, trial: Trial) -> Policy:
        if target in self.policies:
            return self.policies[target]
        fake = trial.fakes.get(target)
        if fake is not None and fake in self.fake_policies:
            return self.fake_policies[fake]
        n = self.syms.name_at(target)
        if n in MODELS:
            return MODELS[n]
        return stub()

    def _dispatcher(self, side: str, trial: Trial, counts: dict, seed: int, trial_no: int):
        lift = self.lift

        def dispatch(m: Machine, addr: int):
            target = addr
            if side == "lift" and lift.lo <= addr < lift.hi:
                if addr not in lift.call_map:
                    m.fault = Fault("exception", addr, f"jumped into the middle of {lift.symbolize(addr)}")
                    raise Stop()
                target = lift.call_map[addr]
            sig = lift.signatures.get(target)
            rec = CallRecord(target, [m.gpr(n) for n in range(3, 11)],
                             [m.gpr64(n) for n in range(3, 11)],
                             [m.fpr(n) for n in range(1, 9)], m.uc.reg_read(_LR) & M32)
            pol = self._policy(target, trial)
            rec.transparent = pol.transparent
            self._derefs(m, rec, sig, pol)
            k = counts.get(target, 0)
            counts[target] = k + 1
            crng = random.Random(hash((seed, trial_no, target, k)))
            ctx = CallCtx(m, rec, crng, sig, side)
            m.calls.append(rec)
            action = pol.handle(ctx)
            if action == "run":
                r = self.syms.func_range(target)
                if r is None:
                    m.fault = Fault("exception", addr, f"run() policy: no size for 0x{target:08X}")
                    raise Stop()
                if r not in m.home:
                    m.home.append(r)
                    m.prescan(*r)
                if target != addr:
                    m.uc.reg_write(_PC, target)
                return
            # clobber what a real callee may clobber, the same way on both sides
            for n in [0] + list(range(5, 13)) + ([] if "r4" in rec.ret else [4]):
                if n != 3 or "r3" not in rec.ret:
                    m.set_gpr(n, crng.getrandbits(32))
            if "r3" not in rec.ret:
                m.set_gpr(3, crng.getrandbits(32))
            for n in [0] + list(range(2, 14)):
                m.set_fpr(n, f32_rounds(crng.uniform(-1e3, 1e3)))
            if "f1" not in rec.ret:
                m.set_fpr(1, f32_rounds(crng.uniform(-1e3, 1e3)))
            m.uc.reg_write(_PC, rec.lr)

        return dispatch

    def _derefs(self, m, rec, sig, pol):
        forced = getattr(pol, "deref", None) or {}
        regs = arg_registers(sig) if sig else []
        for reg, t in regs:
            if t.kind != "ptr" or ":" in reg or reg in forced:
                continue
            p = rec.gpr[int(reg[1:]) - 3]
            if t.const_pointee and STACK_LO <= p < STACK_HI and t.pointee and 0 < t.pointee.size <= 512:
                try:
                    rec.derefs[reg] = (m.read(p, t.pointee.size), t.pointee)
                except Stop:
                    m.fault = None
        for reg, size in forced.items():
            p = rec.gpr[int(reg[1:]) - 3]
            try:
                rec.derefs[reg] = (m.read(p, size), None)
            except Stop:
                m.fault = None

    # ── trials ──────────────────────────────────────────────────────────────
    def make_trial(self, n: int) -> tuple[Trial, dict, list]:
        rng = random.Random(self.opts.seed * 1_000_003 + n)
        t = Trial(rng, self.syms, dwarf=self._dwarf())
        regs = {"gpr": [rng.getrandbits(32) for _ in range(32)],
                "fpr": [f32_rounds(rng.uniform(-1e3, 1e3)) for _ in range(32)],
                "ctr": rng.getrandbits(32), "cr": 0, "gpr64": {}}
        regs["gpr"][1] = STACK_TOP
        regs["gpr"][13] = TLS_BASE
        vregs = [[struct.unpack(">I", struct.pack(">f", rng.uniform(-100, 100)))[0] for _ in range(4)]
                 for _ in range(128)]
        self.spec.inputs(t)
        for reg, v in t.reg_args.items():
            if reg.startswith("r"):
                n_ = int(reg[1:])
                regs["gpr"][n_] = int(v) & M32
                regs["gpr64"][n_] = int(v) & ((1 << 64) - 1)
            elif reg.startswith("f"):
                regs["fpr"][int(reg[1:])] = float(v)
            else:
                raise SystemExit(f"spec: unknown register {reg}")
        t.stack_fill = rng.randbytes(0x9000)
        return t, regs, vregs

    def _dwarf(self):
        if not hasattr(self, "_dw"):
            from .build import llvm_bin
            from .dwarf import Dwarf
            self._dw = Dwarf(str(self.lift.obj), llvm_bin("llvm-dwarfdump"))
        return self._dw

    def initial(self, t: Trial):
        image, lift = self.image, self.lift

        def byte(a):
            for pa, data in t.image_patches.items():
                if pa <= a < pa + len(data):
                    return data[a - pa]
            if IMAGE_BASE <= a < IMAGE_BASE + len(image):
                return image[a - IMAGE_BASE]
            if lift.lo <= a < lift.hi:
                for s in lift.sections:
                    if s.addr <= a < s.addr + s.size:
                        return s.data[a - s.addr]
                return 0
            off = a - ARENA_BASE
            if 0 <= off < len(t.arena):
                return t.arena[off]
            return 0

        return lambda a, n: bytes(byte(a + k) for k in range(n))

    def run_side(self, side: str, t: Trial, regs, vregs, trial_no: int):
        m = self.machine
        uc = m.uc
        if t.arena:
            uc.mem_write(ARENA_BASE, bytes(t.arena))
        for a, data in t.image_patches.items():
            uc.mem_write(a, data)
        uc.mem_write(STACK_TOP - 0x8000, t.stack_fill)
        m.heap_next = 0x48000000
        counts: dict = {}
        if side == "orig":
            entry, home = self.addr, [self.orig_range]
        else:
            entry, home = self.lift.target.addr, list(self.lift_home)
        res = m.run(side, entry, home, self._dispatcher(side, t, counts, self.opts.seed, trial_no),
                    regs, vregs)
        final = {}
        addrs = sorted(res.writes)
        k = 0
        while k < len(addrs):
            s = addrs[k]
            e = s + 1
            k += 1
            while k < len(addrs) and addrs[k] == e:
                e += 1
                k += 1
            data = uc.mem_read(s, e - s)
            for j in range(e - s):
                final[s + j] = data[j]
        res.final = final
        init = self.initial(t)
        m.restore(res.writes.keys(), init)
        for a, data in t.image_patches.items():
            uc.mem_write(a, self.image[a - IMAGE_BASE: a - IMAGE_BASE + len(data)])
        return res

    # ── compare ─────────────────────────────────────────────────────────────
    def feq(self, a: float, b: float) -> bool:
        if a == b or (a != a and b != b):
            return True
        if self.ftol <= 0:
            return False
        return abs(a - b) <= self.ftol * max(1.0, abs(a), abs(b))

    def where(self, side, pc):
        if pc is None:
            return "?"
        if side == "orig":
            lo, hi = self.orig_range
            if lo <= pc < hi:
                return f"0x{pc:08X} ({self.spec.FUNCTION}+0x{pc - lo:X}: {self.orig_insn(pc)})"
            n = self.syms.name_at(pc)
            return f"0x{pc:08X}" + (f" ({n})" if n else "")
        s = self.lift.symbolize(pc)
        return f"0x{pc:08X}" + (f" ({s})" if s else "")

    def orig_insn(self, pc):
        if pc not in self.disasm_cache:
            w = int.from_bytes(self.image[pc - IMAGE_BASE: pc - IMAGE_BASE + 4], "big")
            if (w >> 26) in (4, 5, 6):
                # disasm/sections/.text.s mangles VMX128; name it from the binutils table
                from .isatest import vmx128_name
                name = vmx128_name(w)
                if name:
                    self.disasm_cache[pc] = f"{name} (0x{w:08X})"
                    return self.disasm_cache[pc]
            txt = ""
            path = self.repo / "disasm/sections/.text.s"
            key = f"0x{pc:08X}:".encode()
            try:
                with open(path, "rb") as fh:
                    for line in fh:
                        if line.startswith(key):
                            txt = " ".join(line.decode(errors="replace").split()[1:])
                            break
            except OSError:
                pass
            self.disasm_cache[pc] = txt or "?"
        return self.disasm_cache[pc]

    def describe_addr(self, t: Trial, a: int) -> str:
        r = t.region_of(a)
        if r:
            return r
        if IMAGE_BASE <= a < IMAGE_BASE + len(self.image):
            for base in range(a, a - 0x1000, -1):
                n = self.syms.name_at(base)
                if n:
                    return f"{n}+0x{a - base:X}" if a != base else n
            return "image"
        if self.lift.lo <= a < self.lift.hi:
            return "lift " + (self.lift.symbolize(a) or "data")
        if 0x48000000 <= a < 0x49000000:
            return f"heap+0x{a - 0x48000000:X}"
        return "?"

    def render_arg(self, side, v, t):
        if t is not None and t.kind == "ptr":
            if STACK_LO <= v < STACK_HI:
                return "<stack>"
            s = self._cstring(v)
            if s is not None:
                return repr(s)
        return f"0x{v:08X}"

    def _cstring(self, a):
        m = self.machine
        if not ((IMAGE_BASE <= a < IMAGE_BASE + len(self.image)) or (self.lift.lo <= a < self.lift.hi)):
            return None
        try:
            raw = bytes(m.uc.mem_read(a, 64))
        except Exception:
            return None
        end = raw.find(b"\0")
        if end < 2 or not all(32 <= c < 127 for c in raw[:end]):
            return None
        return raw[:end].decode()

    def compare(self, t: Trial, regs, o, l):
        fn = self.spec.FUNCTION
        # faults
        if o.fault and o.fault.kind == "unsupported":
            raise Unsupported(o.fault)
        if o.fault:
            raise SpecError(f"the original faulted: {o.fault.kind}: {o.fault.detail} at "
                            f"{self.where('orig', o.fault.pc)}", o)
        if l.fault:
            if l.fault.kind == "unsupported":
                raise Unsupported(l.fault)
            raise Divergence(f"the lift faulted: {l.fault.kind}: {l.fault.detail}",
                             [f"at {self.where('lift', l.fault.pc)}",
                              "the original returned normally"])
        # calls
        oc = [c for c in o.calls if not c.transparent]
        lc = [c for c in l.calls if not c.transparent]
        for k in range(max(len(oc), len(lc))):
            a = oc[k] if k < len(oc) else None
            b = lc[k] if k < len(lc) else None
            if a is None or b is None:
                have, side = (a, "original") if a else (b, "lift")
                raise Divergence(
                    f"call #{k + 1}: only the {side} calls {self.call_name(have.target, t)}",
                    self.call_context(oc, lc, k, t))
            if a.target != b.target:
                raise Divergence(
                    f"call #{k + 1}: original calls {self.call_name(a.target, t)}, "
                    f"lift calls {self.call_name(b.target, t)}", self.call_context(oc, lc, k, t))
            self.compare_args(k, a, b, oc, lc, t)
        # return value
        sig = self.lift.target_sig
        ret = getattr(self.spec, "RET", "auto")
        if ret == "auto":
            if sig is None or sig.ret.kind == "void" or sig.ret.kind in ("struct", "array"):
                ret = None
            elif sig.ret.kind == "float":
                ret = "f1"
            elif sig.ret.kind == "int" and sig.ret.size == 8:
                ret = "r3:r4"
            else:
                ret = ("r3", sig.ret.size)
        if ret == "f1" and not self.feq(o.fpr[1], l.fpr[1]):
            raise Divergence(f"{fn} returns f1 = {o.fpr[1]!r} (original) vs {l.fpr[1]!r} (lift)",
                             self.args_line(regs))
        if isinstance(ret, tuple) or ret == "r3":
            size = ret[1] if isinstance(ret, tuple) else 4
            mask = (1 << (8 * size)) - 1
            same_str = (sig is not None and sig.ret.kind == "ptr"
                        and self._cstring(o.gpr[3]) is not None
                        and self._cstring(o.gpr[3]) == self._cstring(l.gpr[3]))
            if (o.gpr[3] & mask) != (l.gpr[3] & mask) and not same_str:
                raise Divergence(f"{fn} returns r3 = 0x{o.gpr[3] & mask:X} (original) vs "
                                 f"0x{l.gpr[3] & mask:X} (lift)", self.args_line(regs))
        if ret == "r3:r4":
            ov = o.gpr64[3]
            lv = (l.gpr[3] << 32) | l.gpr[4]
            if ov != lv:
                raise Divergence(f"{fn} returns 0x{ov:016X} (original) vs 0x{lv:016X} (lift)",
                                 self.args_line(regs))
        # memory
        diffs = []
        init = self.initial(t)
        for a in sorted(set(o.final) | set(l.final)):
            va = o.final.get(a)
            vb = l.final.get(a)
            if va is None:
                va = init(a, 1)[0]
            if vb is None:
                vb = init(a, 1)[0]
            if va != vb:
                diffs.append(a)
        if diffs:
            diffs = self.drop_float_noise(diffs, o, l, t)
        if diffs:
            a = diffs[0]
            w = a & ~3
            def word(res):
                return bytes(res.final.get(w + k, init(w + k, 1)[0]) for k in range(4))
            ow, lw = word(o), word(l)
            lines = [f"at 0x{a:08X} ({self.describe_addr(t, a)}), word 0x{w:08X}: "
                     f"original {ow.hex()}  lift {lw.hex()}"
                     + (f"  (as f32: {struct.unpack('>f', ow)[0]!r} vs {struct.unpack('>f', lw)[0]!r})"
                        if w in t.float_words else ""),
                     f"original wrote it at {self.where('orig', o.writes.get(a))}" if a in o.writes
                     else "original left it unchanged",
                     f"lift wrote it at {self.where('lift', l.writes.get(a))}" if a in l.writes
                     else "lift left it unchanged",
                     f"{len(diffs)} differing byte(s) in total"]
            raise Divergence("memory differs", lines + self.args_line(regs))
        # ABI: callee-saved registers
        for res, side in ((o, "original"), (l, "lift")):
            for n in NONVOLATILE_GPR:
                if n == 2 and side == "lift":
                    continue
                if res.gpr[n] != regs["gpr"][n] & M32:
                    raise Divergence(f"the {side} didn't preserve r{n}",
                                     [f"entry 0x{regs['gpr'][n] & M32:08X}, exit 0x{res.gpr[n]:08X}"])
            for n in NONVOLATILE_FPR:
                if res.fpr[n] != regs["fpr"][n]:
                    raise Divergence(f"the {side} didn't preserve f{n}", [])

    def drop_float_noise(self, diffs, o, l, t):
        if self.ftol <= 0:
            return diffs
        init = self.initial(t)
        keep = []
        for a in diffs:
            w = a & ~3
            if w in t.float_words:
                ov = struct.unpack(">f", bytes(o.final.get(w + k, init(w + k, 1)[0]) for k in range(4)))[0]
                lv = struct.unpack(">f", bytes(l.final.get(w + k, init(w + k, 1)[0]) for k in range(4)))[0]
                if self.feq(ov, lv):
                    continue
            keep.append(a)
        return keep

    def call_name(self, target, t):
        if FAKE_BASE <= target < FAKE_BASE + FAKE_SIZE:
            return t.fakes.get(target, f"0x{target:08X}")
        return self.syms.describe(target)

    def call_context(self, oc, lc, k, t):
        lines = []
        for j in range(max(0, k - 2), min(max(len(oc), len(lc)), k + 3)):
            a = self.call_name(oc[j].target, t) if j < len(oc) else "-"
            b = self.call_name(lc[j].target, t) if j < len(lc) else "-"
            lines.append(f"  #{j + 1:<3} original: {a:<40} lift: {b}")
        return ["call traces:"] + lines

    def compare_args(self, k, a, b, oc, lc, t):
        sig = self.lift.signatures.get(a.target)
        regs = arg_registers(sig) if sig else [("r3", None)]
        forced = getattr(self._policy(a.target, t), "args", None)
        if forced:
            regs = [(r, None) for r in forced]
        name = self.call_name(a.target, t)
        for reg, ty in regs:
            if ty is not None and ty.kind in ("struct", "array"):
                continue
            if reg.startswith("f"):
                n = int(reg[1:]) - 1
                if not self.feq(a.fpr[n], b.fpr[n]):
                    raise Divergence(f"call #{k + 1} to {name}: {reg} = {a.fpr[n]!r} (original) vs "
                                     f"{b.fpr[n]!r} (lift)", self.call_context(oc, lc, k, t))
                continue
            if ":" in reg:
                hi, lo = (int(x[1:]) - 3 for x in reg.split(":"))
                av = a.gpr64[hi]
                bv = (b.gpr[hi] << 32) | b.gpr[lo]
                if av != bv:
                    raise Divergence(f"call #{k + 1} to {name}: 64-bit arg 0x{av:X} vs 0x{bv:X}",
                                     self.call_context(oc, lc, k, t))
                continue
            n = int(reg[1:]) - 3
            size = ty.size if ty is not None and ty.kind == "int" else 4
            mask = (1 << (8 * size)) - 1
            av, bv = a.gpr[n] & mask, b.gpr[n] & mask
            ra = self.render_arg("orig", av, ty)
            rb = self.render_arg("lift", bv, ty)
            if ty is not None and ty.kind == "ptr":
                same = ra == rb
            else:
                same = av == bv
            if not same:
                raise Divergence(f"call #{k + 1} to {name}: {reg} = {ra} (original) vs {rb} (lift)",
                                 self.call_context(oc, lc, k, t))
        for reg in sorted(set(a.derefs) | set(b.derefs)):
            da, ty = a.derefs.get(reg, (None, None))
            db, _ = b.derefs.get(reg, (None, None))
            if da is None or db is None or da == db:
                continue
            from .dwarf import field_path, float_offsets
            fl = float_offsets(ty) if ty is not None else {}
            for off in range(0, min(len(da), len(db))):
                if da[off] == db[off]:
                    continue
                fo = next((fo for fo, sz in fl.items() if fo <= off < fo + sz and sz == 4), None)
                if fo is not None:
                    x = struct.unpack(">f", da[fo:fo + 4])[0]
                    y = struct.unpack(">f", db[fo:fo + 4])[0]
                    if self.feq(x, y):
                        continue
                    path = field_path(ty, fo)
                    raise Divergence(f"call #{k + 1} to {name}: *{reg} differs at +0x{fo:X}"
                                     f"{f' ({ty.name}.{path})' if path else ''}: "
                                     f"{x!r} (original) vs {y!r} (lift)",
                                     [f"original *{reg}: {da.hex()}", f"lift     *{reg}: {db.hex()}"])
                path = field_path(ty, off)
                raise Divergence(f"call #{k + 1} to {name}: *{reg} differs at +0x{off:X}"
                                 f"{f' ({ty.name}.{path})' if path else ''}",
                                 [f"original *{reg}: {da.hex()}", f"lift     *{reg}: {db.hex()}"])

    def args_line(self, regs):
        g = regs["gpr"]
        sig = self.lift.target_sig
        if sig is None:
            return [f"inputs: r3=0x{g[3]:08X} r4=0x{g[4]:08X} r5=0x{g[5]:08X} f1={regs['fpr'][1]!r}"]
        parts = []
        for reg, ty in arg_registers(sig):
            if reg.startswith("f"):
                parts.append(f"{reg}={regs['fpr'][int(reg[1:])]!r}")
            elif ":" not in reg:
                parts.append(f"{reg}=0x{g[int(reg[1:])]:08X}")
        return ["inputs: " + " ".join(parts)]

    def dump(self, t, regs, o, l):
        print("  inputs: " + " ".join(f"{k}={v:#x}" if isinstance(v, int) else f"{k}={v!r}"
                                     for k, v in t.reg_args.items()))
        for res, side in ((o, "original"), (l, "lift")):
            print(f"  {side} calls:")
            for c in res.calls:
                args = " ".join(f"r{3 + k}={v:08X}" for k, v in enumerate(c.gpr[:4]))
                ret = " ".join(f"{k}={v:#x}" if isinstance(v, int) else f"{k}={v!r}" for k, v in c.ret.items())
                tag = " (model)" if c.transparent else ""
                print(f"    {self.call_name(c.target, t)}{tag}: {args} f1={c.fpr[0]!r} -> {ret or '-'}")
            print(f"  {side} wrote {len(res.final)} byte(s) outside the stack")

    # ── main loop ───────────────────────────────────────────────────────────
    def run(self) -> int:
        out = sys.stdout
        todo = [self.opts.only] if self.opts.only is not None else range(self.trials)
        for n in todo:
            t, regs, vregs = self.make_trial(n)
            o = self.run_side("orig", t, regs, vregs, n)
            l = self.run_side("lift", t, regs, vregs, n)
            try:
                self.compare(t, regs, o, l)
            except Divergence as d:
                if self.opts.verbose:
                    self.dump(t, regs, o, l)
                print(f"FAIL {self.name}: trial {n} (seed {self.opts.seed}): {d.title}", file=out)
                for line in d.lines:
                    print(f"  {line}", file=out)
                print(f"  rerun: lift-check {self.name} --seed {self.opts.seed} --only {n} -v", file=out)
                return 1
            except Unsupported as u:
                f = u.args[0]
                print(f"UNSUPPORTED {self.name}: unsupported: {f.detail} at "
                      f"{self.where('orig', f.pc) if f.pc < 0x82800000 else self.where('lift', f.pc)}",
                      file=out)
                return 3
            except SpecError as e:
                print(f"SPEC {self.name}: trial {n}: {e.args[0]}", file=out)
                if o.calls:
                    print("  calls the original made before that:", file=out)
                    for c in o.calls[-4:]:
                        pol = self._policy(c.target, t)
                        how = "default stub, random return" if type(pol) is stub and pol.ret_ is None \
                            else type(pol).__name__
                        ret = " ".join(f"{k}=0x{v:08X}" if isinstance(v, int) else f"{k}={v:g}"
                                       for k, v in c.ret.items())
                        print(f"    {self.call_name(c.target, t)} -> {ret or '-'} ({how})", file=out)
                print("  fix the spec's inputs or CALLS so the original runs cleanly", file=out)
                return 2
            if self.opts.verbose:
                calls = [self.call_name(c.target, t) for c in o.calls if not c.transparent]
                print(f"  trial {n}: ok, {len(o.final)} bytes written, calls: {', '.join(calls) or '-'}")
        if self.opts.only is not None:
            if not self.opts.quiet:
                print(f"PASS {self.name}: trial {self.opts.only} (seed {self.opts.seed})", file=out)
            return 0
        ftxt = f", floats within {self.ftol:g}" if self.ftol > 0 else ""
        if not self.opts.quiet:
            print(f"PASS {self.name}: {self.trials} trials (seed {self.opts.seed}{ftxt})", file=out)
        return 0


class Unsupported(Exception):
    pass


class SpecError(Exception):
    pass

