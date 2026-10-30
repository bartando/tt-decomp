"""grcDevice_SetStencilEnable: RB_DEPTHCONTROL switch, with and without a depth surface bound."""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetStencilEnable"
ADDRESS = 0x823541F0
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1000
RET = None


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3200, "device")
    t.w32(device + 0x3108, rng.choice([0, t.u32()]))
    t.w32(device + 0x2D74, t.u32())
    t.w32(device + 0x2EC8, t.u32())
    t.w64(device + 0x28, rng.choice([0, rng.getrandbits(64)]))
    t.w64(device + 0x30, rng.choice([0, rng.getrandbits(64)]))
    t.args(r3=device, r4=rng.choice([0, 1, 2, 3, t.u32()]))
