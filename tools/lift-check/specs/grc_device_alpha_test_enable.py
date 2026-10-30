"""grcDevice_SetAlphaTestEnable: one register field at +0x2D7C and its dirty bits."""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetAlphaTestEnable"
ADDRESS = 0x82353AA0
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1000
RET = None


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3200, "device")
    t.w32(device + 0x2D7C, t.u32())
    t.w64(device + 0x28, rng.choice([0, rng.getrandbits(64)]))
    t.w64(device + 0x30, rng.choice([0, rng.getrandbits(64)]))
    t.args(r3=device, r4=rng.choice([0, 1, 2, 7, 15, rng.randrange(256), t.u32()]))
