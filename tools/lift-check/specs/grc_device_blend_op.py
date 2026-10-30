"""grcDevice_SetBlendOp: RB_BLENDCONTROL state, with blending and separate alpha on and off.

The stored control word, flags and dirty mask are random, so the alpha mirror sees
every factor pattern.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetBlendOp"
ADDRESS = 0x82353B88
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1000
RET = None


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3000, "device")
    t.w32(device + 0x2CB8, t.u32())
    t.w32(device + 0x2CBC, (rng.randrange(4) << 30) | rng.getrandbits(30))
    t.w64(device + 0x28, rng.choice([0, rng.getrandbits(64)]))
    t.args(r3=device, r4=rng.choice([0, 1, rng.randrange(32), t.u32()]))
