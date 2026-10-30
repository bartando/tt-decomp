"""grcDevice_SetColorWriteEnable: one register field at +0x2D1C and its dirty bits."""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetColorWriteEnable"
ADDRESS = 0x823547A0
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1000
RET = None


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3200, "device")
    t.w32(device + 0x2D1C, t.u32())
    t.w64(device + 0x28, rng.choice([0, rng.getrandbits(64)]))
    t.w64(device + 0x30, rng.choice([0, rng.getrandbits(64)]))
    t.w32(device + 0x30F8, rng.choice([0, t.u32()]))
    t.w32(device + 0x2EB4, t.u32())
    t.args(r3=device, r4=rng.choice([0, 1, 2, 7, 15, rng.randrange(256), t.u32()]))
