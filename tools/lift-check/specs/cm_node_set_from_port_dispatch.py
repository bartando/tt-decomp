"""0x82275380 dispatches on the destination's byte +16, not argument r5.

Every dimension, invalid tags, scalar/byte write widths, vector temporary,
callee arguments, return buffer and untouched destination bytes are compared.
"""
import struct
from liftcheck.spec import *

FUNCTION = "rage::cmNode_SetFromPort_Dispatch"
ADDRESS = 0x82275380
SOURCE = "src/rage/misc/rage_cm.cpp"
TRIALS = 1200
RET = None
EXTERNS = {
    "rage::cmNode_GetDim": 0x82184B60,
    "rage::cmNode_GetFloat": 0x82179350,
    "rage::cmNode_GetBool": 0x822621B0,
    "rage::cmNode_GetVector": 0x821792D8,
    "rage::cmNode_GetInt": 0x82184BD8,
}


def payload(ctx):
    return int.from_bytes(ctx.read(ctx.r(3), 4), "big")


def get_dim(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(payload(ctx), 4), "big"))


def get_float(ctx):
    ctx.ret(f1=struct.unpack(">f", ctx.read(payload(ctx) + 4, 4))[0])


def get_bool(ctx):
    ctx.ret(r3=ctx.read(payload(ctx) + 8, 1)[0])


def get_int(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(payload(ctx) + 12, 4), "big"))


def get_vector(ctx):
    port = ctx.r(4)
    data = int.from_bytes(ctx.read(port, 4), "big")
    ctx.write(ctx.r(3), ctx.read(data + 16, 16))
    ctx.ret(r3=ctx.r(3))


CALLS = {
    0x82184B60: model(get_dim, args=("r3",), deref={"r3": 8}),
    0x82179350: model(get_float, args=("r3",), deref={"r3": 8}),
    0x822621B0: model(get_bool, args=("r3",), deref={"r3": 8}),
    0x821792D8: model(get_vector, args=("r3", "r4"), deref={"r4": 8}),
    0x82184BD8: model(get_int, args=("r3",), deref={"r3": 8}),
}


def inputs(t):
    dst = t.alloc(64, "destination_with_guards") + 16
    port = t.alloc(8, "port")
    data = t.alloc(32, "callee_results")
    t.w32(port, data)
    t.w32(port + 4, t.rng.choice((0, 1, 2, 3, t.u32())))
    t.wf32(data + 4, t.rng.uniform(-1e6, 1e6))
    dim = t.rng.choice((0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 255, t.rng.randrange(256)))
    t.w8(dst + 16, dim)
    # r5 deliberately disagrees with the tag: it is not an input to the asm.
    t.args(r3=dst, r4=port, r5=t.rng.choice((0, 1, 2, 3, 4, 5, t.u32())))
