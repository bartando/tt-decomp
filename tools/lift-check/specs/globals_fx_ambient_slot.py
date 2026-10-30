"""Compare with the live mapped slot; never update a private previous-request mirror."""
from liftcheck.spec import *

FUNCTION = "fxAmbient::RequestStreamSlot"
ADDRESS = 0x82112B00
SOURCE = "src/graphics/fx_effects.cpp"


def inputs(t):
    cap = t.rng.randrange(0, 16)
    request = t.pick([-1, 0, cap, cap + 1, t.rng.randrange(0, 16)])
    t.w32(0x825C8F54, cap)
    t.w32(0x825EBB84, t.pick([0, min(request, cap), t.rng.randrange(16)]) & 0xFFFFFFFF)
    t.w32(0x825EBB1C, t.u32())
    t.w32(0x825EBBDC, t.u32())
    t.args(r3=request & 0xFFFFFFFF)
