"""GPU buffer release (data +0xC, flags +0x1C): reference drop, kernel device hand-back, owned frees.

Reference counts of 1 (last) and others, with and without a data block, both
process types picking VdGlobalDevice or VdGlobalXamDevice, null kernel devices,
zero handles (out-param contents compared), and every combination of the two
ownership flags in +0x1C (bit 31 frees the data, bit 30 the buffer).
"""
from liftcheck.spec import *

FUNCTION = "grcGpuBuffer_Release"
ADDRESS = 0x82356CF0
SOURCE = "src/graphics/grc_device.cpp"


def _process_type(ctx):
    ctx.ret(r3=ctx.rng.choice([0, 1, 2, 2, 3]))


CALLS = {
    0x82585E9C: model(_process_type),
    0x82566B78: stub(args=()),
    0x8235AA78: stub(ret="void", args=("r3", "r4"), deref={"r4": 4}),
    0x820C02D0: stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    res = t.alloc(0x40, "buffer")
    for k in range(0x40 // 4):
        t.w32(res + 4 * k, t.u32())
    t.w32(res + 4, rng.choice([1, 1, 1, 0, 2, t.u32()]))
    t.w32(res + 0xC, rng.choice([0, t.u32() | 1]))
    t.w32(res + 8, rng.choice([0, t.u32()]))
    t.w32(res + 0x1C, (t.u32() & 0x3FFFFFFF) | rng.choice([0, 0x80000000, 0x40000000, 0xC0000000]))
    for slot, name in ((0x82000730, "vd_device"), (0x82000734, "vd_xam_device")):
        var = t.alloc(4, name)
        t.w32(var, rng.choice([0, t.alloc(0x40, name + "_obj")]))
        t.w32(slot, var)
    t.args(r3=res)
TRIALS = 1000
