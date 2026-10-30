"""Slot 6: publication, all variant sources, flush latches and both bind paths.

Every table word is distinct. Direct entries also exercise otherwise unusable
variant/pass indices: that path must not touch the technique table.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::grmShaderFx::Dispatch"
ADDRESS = 0x820EFA08
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000


def published(ctx):
    shader = struct.unpack(">I", ctx.read(0x825EBA68, 4))[0]
    assert ctx.read(shader + 44, 4) == ctx.read(0x825C9010, 4), "frame not published before call"
    return shader


def flush(ctx):
    published(ctx)


def bind(ctx):
    assert ctx.r(3) == published(ctx) + 16, "wrong effect slot / active shader"
    ctx.ret(r3=ctx.rng.getrandbits(32))


CALLS = {
    "grcDevice_FlushRenderState": model(flush, args=()),
    "grmShaderInstance_Bind": model(bind, args=("r3", "r4", "r5"), deref={"r3": 52}),
}


def inputs(t):
    rng = t.rng
    shader = t.alloc(80, "shader")
    table = t.alloc(4096, "technique table")
    # Keep the effective table offset bounded while testing PPC shift wrapping.
    variants = [rng.randrange(32) | rng.choice([0, 0x40000000, 0x80000000])
                for _ in range(3)]
    mode = rng.randrange(3)
    t.w32(0x825C9A5C, variants[0] if mode == 0 else -1)
    t.w32(0x825EBBDC, 0 if mode == 2 else rng.choice([1, 0x80000000, t.u32() | 1]))
    t.w32(0x825C9A60, variants[1])
    t.w32(0x825C9A64, variants[2])
    t.w32(0x825EBA68, t.u32())
    t.w32(0x825C9010, t.u32())
    latch_mode = rng.randrange(4)
    t.w32(0x825EBB1C, rng.choice([1, 0x100, 0x80000000, t.u32() | 1]) if latch_mode & 1 else 0)
    t.w32(0x825EBAB4, rng.choice([1, 0x100, 0x80000000, t.u32() | 1]) if latch_mode & 2 else 0)
    for i in range(1024):
        t.w32(table + i * 4, (i << 18) | 0x12345)
    direct = rng.choice([0, 0, 1, 0x80000000, 0xffffffff, t.u32() | 1])
    if direct:
        # Deliberately invalid: direct entries must bypass the table entirely.
        t.w32(shader + 64, 0)
        pass_index = t.u32()
    else:
        t.w32(shader + 64, table)
        pass_index = rng.choice([0, 1, 3, 4, 127, rng.randrange(128)])
    t.args(r3=shader, r4=pass_index, r5=t.u32(), r6=direct)
