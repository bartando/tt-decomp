"""cmChanged slot 10: dimension routing, suppression, history and byte widths.

Execute retail integer/byte evaluators for real direct and virtual ports. Cover
supported dimensions 1/3/5, unsupported full-width node dimensions and invalid
port tags with null payloads. Equal/different history, noncanonical bool bytes
and suppression bytes, and all surrounding data compare without ignores.
Only virtual evaluator out-parameters are modelled; caller r4 is irrelevant.
"""
from liftcheck.spec import *

FUNCTION = "rage::cmChanged::Tick"
ADDRESS = 0x82277EF0
SOURCE = "src/rage/misc/rage_cm.cpp"
TRIALS = 1600
RET = None
EXTERNS = {"rage::cmNode_GetBool": 0x822621B0}


def get_word(ctx):
    ctx.write(ctx.r(4), ctx.read(ctx.r(3) + 8, 4))
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 12, 4), "big"))


def get_byte(ctx):
    ctx.write(ctx.r(4), ctx.read(ctx.r(3) + 8, 1))
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 12, 4), "big"))


CALLS = {0x82184B60: run(args=("r3",), deref={"r3": 8}),
         0x82184BD8: run(args=("r3",), deref={"r3": 8}),
         0x822621B0: run(args=("r3",), deref={"r3": 8}),
         "input.vfn_1": model(get_word, args=("r3", "r4")),
         "input.vfn_3": model(get_byte, args=("r3", "r4")),
         "input.vfn_5": model(get_word, args=("r3", "r4"))}


def inputs(t):
    r = t.rng
    obj = t.alloc(56, "changedNodeAndGuards") + 4
    output = t.alloc(16, "changedByteAndGuards") + 4
    previous = t.alloc(16, "previousValueAndGuards") + 4
    source = t.alloc(32, "sourceAndGuards") + 4
    kind = (1, 2, 1, 2, 0, 3, 0x101, 0x102, 0xffffffff)[t.index % 9]
    dim = (1, 3, 5, 0, 2, 4, 6, 255, 0x101, 0x103, 0x105,
           0xffffffff)[(t.index // 9) % 12]
    value = r.choice((0, 1, 2, 0x7fffffff, 0x80000000, 0xffffffff, t.u32()))
    if dim == 3:
        value = r.choice((0, 1, 2, 0x7f, 0x80, 0xfe, 0xff)) << 24 | r.getrandbits(24)
    t.w32(source, value)
    t.w8(source + 16, dim & 255)
    upstream = t.alloc(24, "upstreamNode")
    t.w32(upstream, t.vtable("input"))
    t.w32(upstream + 4, dim)
    t.w32(upstream + 8, value)
    t.w32(upstream + 12, value ^ 0xa5a5a5a5)
    t.w32(obj + 12, source if kind == 1 else upstream if kind == 2 else 0)
    t.w32(obj + 16, kind)
    t.w32(obj + 24, output)
    t.w32(obj + 32, previous)
    t.w8(obj + 36, r.choice((0, 0, 0, 1, 2, 0x80, 0xff)))
    # Half equal history; byte comparisons also see different low 24 bits.
    t.w32(previous, value if t.index % 2 else value ^ 0xffffffff)
    if dim == 3 and t.index % 3 == 0:
        t.w32(previous, (value & 0xff000000) | r.getrandbits(24))
    t.args(r3=obj, r4=t.u32())
