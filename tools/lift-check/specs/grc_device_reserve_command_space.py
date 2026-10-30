"""Command-ring reservation: aligned and block modes, wraps, fence refusals.

The device is a buffer with the ring fields set around one 64KB ring; cursors,
the GPU fence and its sequence are placed before, at and after the requested
block so every refusal and wrap branch runs. The commit helper is a stub.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_ReserveCommandSpace"
ADDRESS = 0x82359E80
SOURCE = "src/graphics/grc_device.cpp"
CALLS = {0x82359DC0: stub(ret="void", args=("r3", "r4", "r5"))}


def inputs(t):
    rng = t.rng
    dev = t.alloc(14032, "device")
    ring = 0x10000000
    start, end = ring, ring + 0x10000
    pick = lambda: rng.choice([0, start, end - rng.choice([0, 4, 32, 256, 4096]),
                               start + rng.randrange(0x10000), end + 64])
    t.w32(dev + 0, start - 4)
    t.w32(dev + 4, start - 52)
    t.w32(dev + 14004, start)
    t.w32(dev + 14008, end)
    t.w32(dev + 14012, rng.choice([0, 64, 256, 1024, 4096]))
    t.w32(dev + 14016, pick())
    seq = t.u32()
    t.w32(dev + 14020, seq)
    t.w32(dev + 14024, pick())
    t.w32(dev + 14028, rng.choice([end, start + rng.randrange(0x10000)]))
    t.w32(dev + 13536, rng.choice([0, pick()]))
    t.w32(dev + 13540, (seq + rng.choice([-1, 0, 1, 2])) & 0xFFFFFFFF)
    t.w8(dev + 10434, rng.randrange(256))
    size = t.alloc(4, "size")
    t.w32(size, rng.choice([0, 4, 16, 64, 200, 4096, 0x10000, rng.randrange(0x20000)]))
    t.args(r3=t.u32(), r4=dev, r5=rng.choice([0, 1, t.u32()]), r6=size,
           r7=rng.choice([1, 4, 16, 32, 128]))
