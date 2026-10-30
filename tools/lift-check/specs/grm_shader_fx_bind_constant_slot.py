"""Slot 8: descriptor indexing and all four context/instance cache states.

Includes negative and wrapping indices whose PPC byte offsets stay in bounds.
Call snapshots check the descriptor and instance; commit checks publication order.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::grmShaderFx::BindConstantSlot"
ADDRESS = 0x820EF928
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000


def commit(ctx):
    assert ctx.read(0x825EBC50, 4) == struct.pack(">I", ctx.r(3)), "instance not published before commit"
    shader = struct.unpack(">I", ctx.read(0x825EBA68, 4))[0]
    assert ctx.read(shader + 32, 4) == ctx.read(0x825EBC54, 4), "context not cached before commit"


CALLS = {
    "rage_8C48": stub(ret="void", args=("r3", "r4"), deref={"r3": 704}),
    "grmShaderInstance_FilterAndUploadParameters": model(commit, args=("r3",), deref={"r3": 704}),
}


def inputs(t):
    rng = t.rng
    shader = t.alloc(80, "shader")
    instance = t.alloc(704, "active instance")
    other = t.alloc(704, "other instance")
    table = t.alloc(512, "parameter table")
    for i in range(128):
        t.w32(table + 4 * i, (i << 18) | 0x23456)
    # The original adds 3 and shifts left by 2, both modulo 2**32.
    var_index = rng.choice([-3, -2, -1, 0, 1, 4, 28, 124,
                            0x3ffffffd, 0x7ffffffd, 0xfffffffd,
                            rng.randrange(125)])
    t.w32(instance + 516, table)
    context = t.u32()
    mode = rng.randrange(4)
    t.w32(shader + 32, context if mode & 1 else context ^ 0x80000001)
    t.w32(0x825EBA68, shader)
    t.w32(0x825EBC4C, instance)
    t.w32(0x825EBC50, instance if mode & 2 else other)
    t.w32(0x825EBC54, context)
    t.args(r3=shader, r4=var_index & 0xffffffff)
