"""What a spec file imports: input builders and call policies.

A spec is a Python file in tools/lift-check/specs/ with:

    FUNCTION = "StlString::Append"          # name of the lift in SOURCE (or mangled)
    ADDRESS  = 0x8222D5E8                   # the original
    SOURCE   = "src/rage/io/fiAsciiTokenizer.cpp"

    def inputs(t):                          # called once per trial
        s = t.alloc(0x18, "str")
        ...
        t.args(r3=s, r4=first, r5=last)

and optionally CALLS (policies for callees, by name or address), EXTERNS (extra
symbol -> address mappings for the link), FTOL (float tolerance), TRIALS.
"""
from __future__ import annotations

import random
import struct

from .machine import ARENA_BASE, ARENA_SIZE, FAKE_BASE, STACK_HI, STACK_LO, STACK_TOP

__all__ = ["stub", "returns", "alloc", "run", "model", "fail", "MODELS"]


# ── inputs ───────────────────────────────────────────────────────────────────

class Trial:
    """Builds one trial's registers and memory. `t.rng` is the trial's RNG."""

    def __init__(self, rng: random.Random, symbols, dwarf=None):
        self.rng = rng
        self.syms = symbols
        self.dwarf = dwarf
        self.arena = bytearray()
        self.regions: list[tuple[int, int, str, object]] = []   # (addr, size, name, TypeInfo)
        self.float_words: set[int] = set()                  # addresses of f32 words
        self.double_words: set[int] = set()
        self.reg_args: dict[str, object] = {}
        self.image_patches: dict[int, bytes] = {}
        self.fakes: dict[int, str] = {}
        self._fake_next = FAKE_BASE + 0x100
        self.ignored: list[tuple[int, int]] = []
        self.stack_patches: dict[int, bytes] = {}

    # memory -----------------------------------------------------------------
    def alloc(self, size: int, name: str = "", fill: str | bytes = "random", align: int = 16,
              ctype: str | None = None, floats: list | None = None) -> int:
        """Reserves input memory. fill: 'random', 'zero' or bytes. ctype: a struct name in
        the lift; its float members compare with tolerance."""
        off = (len(self.arena) + align - 1) & ~(align - 1)
        if off + size > ARENA_SIZE:
            raise ValueError("arena full")
        self.arena.extend(bytes(off - len(self.arena)))
        if fill == "random":
            data = self.rng.randbytes(size)
        elif fill == "zero":
            data = bytes(size)
        else:
            data = bytes(fill)[:size].ljust(size, b"\0")
        self.arena.extend(data)
        addr = ARENA_BASE + off
        self.regions.append((addr, size, name or f"alloc{len(self.regions)}", None))
        if ctype:
            self.mark_type(addr, ctype)
            self.regions[-1] = (addr, size, self.regions[-1][2], self.dwarf.struct_named(ctype))
        for spec in floats or ():
            o, n = spec if isinstance(spec, tuple) else (spec, 1)
            for k in range(n):
                self.float_words.add(addr + o + 4 * k)
        return addr

    def mark_type(self, addr: int, ctype: str):
        from .dwarf import float_offsets
        t = self.dwarf.struct_named(ctype) if self.dwarf else None
        if t is None:
            raise ValueError(f"no struct '{ctype}' in the lift's debug info")
        for off, size in float_offsets(t).items():
            (self.float_words if size == 4 else self.double_words).add(addr + off)

    def _off(self, addr):
        off = addr - ARENA_BASE
        if not 0 <= off < len(self.arena):
            return None
        return off

    def put(self, addr: int, data: bytes):
        off = self._off(addr)
        if off is None:
            if 0x82000000 <= addr < 0x82800000:
                self.image_patches[addr] = bytes(data)
                return
            if STACK_LO <= addr < STACK_HI:
                self.stack_patches[addr] = bytes(data)     # over the random fill
                return
            raise ValueError(f"0x{addr:08X} isn't in an alloc() or the image")
        self.arena[off: off + len(data)] = data

    def w8(self, a, v): self.put(a, struct.pack(">B", v & 0xFF))
    def w16(self, a, v): self.put(a, struct.pack(">H", v & 0xFFFF))
    def w32(self, a, v): self.put(a, struct.pack(">I", v & 0xFFFFFFFF))
    def w64(self, a, v): self.put(a, struct.pack(">Q", v & 0xFFFFFFFFFFFFFFFF))

    def wf32(self, a, x):
        self.put(a, struct.pack(">f", x))
        self.float_words.add(a)

    def wf64(self, a, x):
        self.put(a, struct.pack(">d", x))
        self.double_words.add(a)

    def floats(self, addr: int, count: int, lo: float = -100.0, hi: float = 100.0):
        for k in range(count):
            self.wf32(addr + 4 * k, self.rng.uniform(lo, hi))

    @property
    def sp(self) -> int:
        """r1 at entry: t.w32(t.sp + 0x54, v) writes the caller's frame (stack arguments)."""
        return STACK_TOP

    def ignore(self, addr: int, size: int = 4):
        """Leave [addr, addr+size) out of this trial's memory comparison."""
        self.ignored.append((addr, size))

    # registers and symbols --------------------------------------------------
    def args(self, **regs):
        """t.args(r3=ptr, r4=7, f1=0.5)"""
        self.reg_args.update(regs)

    def sym(self, name: str) -> int:
        return self.syms.by_name[name]

    def fake_fn(self, name: str) -> int:
        """An address that, when called, is recorded under `name` and handled like a stub."""
        a = self._fake_next
        self._fake_next += 0x10
        self.fakes[a] = name
        return a

    def vtable(self, name: str, slots: int = 16) -> int:
        """A table of `slots` fake functions named name.vfn_<k>; returns its address."""
        tbl = self.alloc(4 * slots, f"{name}.vtable", fill="zero", align=4)
        for k in range(slots):
            self.w32(tbl + 4 * k, self.fake_fn(f"{name}.vfn_{k}"))
        return tbl

    # random values ----------------------------------------------------------
    def f32(self, lo=-100.0, hi=100.0):
        return self.rng.uniform(lo, hi)

    def u32(self):
        return self.rng.getrandbits(32)

    def pick(self, seq):
        return self.rng.choice(list(seq))

    def region_of(self, addr: int) -> str | None:
        from .dwarf import field_path
        for a, n, name, ty in self.regions:
            if a <= addr < a + n:
                path = field_path(ty, addr - a) if ty is not None else ""
                return f"{name}+0x{addr - a:X}" + (f" ({ty.name}.{path})" if path else "")
        return None


# ── call policies ────────────────────────────────────────────────────────────

class Policy:
    transparent = False   # left out of the call-trace comparison
    preserves = ()        # volatile registers the callee leaves alone (beyond a leaf's own)
    args = None           # registers to compare (default: the lift's declaration)
    deref = None          # {reg: size} to compare what they point at

    def handle(self, ctx):  # returns 'return' or 'run'
        raise NotImplementedError


class CallCtx:
    """What a policy sees: the call's registers, memory, an RNG shared by both sides."""

    def __init__(self, machine, record, rng, sig, side):
        self.m = machine
        self.rec = record
        self.rng = rng
        self.sig = sig
        self.side = side

    def r(self, n: int) -> int:
        return self.rec.gpr[n - 3]

    def f(self, n: int) -> float:
        return self.rec.fpr[n - 1]

    def ret(self, r3=None, f1=None):
        if r3 is not None:
            self.m.set_gpr(3, r3)
            self.rec.ret["r3"] = r3 & 0xFFFFFFFF
        if f1 is not None:
            self.m.set_fpr(1, f1)
            self.rec.ret["f1"] = f1

    def read(self, addr, n):
        return self.m.read(addr, n)

    def write(self, addr, data):
        self.m.write(addr, data)

    def alloc(self, n):
        return self.m.alloc(n)

    @staticmethod
    def in_stack(addr):
        return STACK_LO <= addr < STACK_HI


def _fill_type(rng, t, size):
    """Deterministic bytes for a struct the callee writes: floats get floats."""
    from .dwarf import float_offsets
    buf = bytearray(rng.randbytes(size))
    if t is not None:
        for off, sz in float_offsets(t).items():
            if off + sz <= size:
                buf[off:off + sz] = struct.pack(">f" if sz == 4 else ">d", rng.uniform(-10, 10))
    return bytes(buf)


class stub(Policy):
    """Records the call and returns. ret: None (random r3 and f1), a value, 'void', or
    callable(ctx) -> value. out: {'r4': size} fills what r4 points at with random data.
    By default non-const pointer arguments into the stack (out-params) get filled."""

    def __init__(self, ret=None, out=None, deref=None, args=None, auto_out=True, preserves=()):
        self.ret_ = ret
        self.out = out or {}
        self.deref = deref or {}
        self.args = args
        self.auto_out = auto_out
        self.preserves = tuple(preserves)

    def handle(self, ctx):
        from .dwarf import arg_registers
        fills = dict(self.out)
        if self.auto_out and ctx.sig is not None:
            for reg, t in arg_registers(ctx.sig):
                if t.kind == "ptr" and not t.const_pointee and reg.startswith("r") and ":" not in reg:
                    p = ctx.r(int(reg[1:]))
                    if ctx.in_stack(p) and t.pointee is not None and 0 < t.pointee.size <= 512:
                        fills.setdefault(reg, (t.pointee.size, t.pointee))
        for reg, spec in fills.items():
            size, t = spec if isinstance(spec, tuple) else (spec, None)
            ctx.write(ctx.r(int(reg[1:])), _fill_type(ctx.rng, t, size))
        r = self.ret_
        if callable(r):
            r = r(ctx)
        if r == "void":
            return "return"
        if r is None:
            ctx.ret(r3=ctx.rng.getrandbits(32), f1=ctx.rng.uniform(-100, 100))
        elif isinstance(r, float):
            ctx.ret(f1=r)
        else:
            ctx.ret(r3=r)
        return "return"


def returns(value):
    """stub that returns a fixed value (int -> r3, float -> f1)."""
    return stub(ret=value)


class alloc(stub):
    """Returns a fresh zeroed heap block, sized by a register (or `size`)."""

    def __init__(self, size_reg: str | None = "r3", size: int | None = None, **kw):
        super().__init__(**kw)
        self.size_reg, self.size = size_reg, size

    def handle(self, ctx):
        n = self.size if self.size is not None else ctx.r(int(self.size_reg[1:]))
        n = max(1, min(n, 0x100000))
        ctx.ret(r3=ctx.alloc(n))
        return "return"


class run(Policy):
    """Runs the callee's original code (both sides run the same thing). transparent:
    leave it out of the call trace (a helper the lift calls and the original inlines)."""

    def __init__(self, transparent=False):
        if transparent:
            self.transparent = True

    def handle(self, ctx):
        return "run"


class model(Policy):
    """A Python stand-in: fn(ctx) does the work and calls ctx.ret(...). An assertion
    in fn fails the trial (lift side) or reports a SPEC problem (original side)."""

    def __init__(self, fn, transparent=False, args=None, deref=None, preserves=()):
        self.fn = fn
        self.transparent = transparent
        self.args = args
        self.deref = deref or {}
        self.preserves = tuple(preserves)

    def handle(self, ctx):
        self.fn(ctx)
        return "return"


class fail(Policy):
    def handle(self, ctx):
        raise AssertionError(f"call to {ctx.rec.target:#x} that the spec says can't happen")


def _memcpy(ctx):
    d, s, n = ctx.r(3), ctx.r(4), ctx.r(5)
    if n:
        ctx.write(d, ctx.read(s, n))
    ctx.ret(r3=d)


def _memset(ctx):
    d, c, n = ctx.r(3), ctx.r(4), ctx.r(5)
    if n:
        ctx.write(d, bytes([c & 0xFF]) * n)
    ctx.ret(r3=d)


def _cstr(ctx, a):
    out = bytearray()
    while (c := ctx.read(a + len(out), 1)) != b"\0":
        out += c
    return bytes(out)


def _strcmp(ctx):
    x, y = _cstr(ctx, ctx.r(3)), _cstr(ctx, ctx.r(4))
    ctx.ret(r3=(x > y) - (x < y))


def _strlen(ctx):
    a, n = ctx.r(3), 0
    while ctx.read(a + n, 1) != b"\0":
        n += 1
    ctx.ret(r3=n)


MODELS = {
    "memcpy": model(_memcpy, transparent=True),
    "memmove": model(_memcpy, transparent=True),
    "memset": model(_memset, transparent=True),
    "strlen": model(_strlen, transparent=True),
    "strcmp": model(_strcmp, transparent=True),
}
