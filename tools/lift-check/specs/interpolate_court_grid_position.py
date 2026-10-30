"""0x8219E590: court-grid interpolation, including the existing output w lane."""
from liftcheck.spec import *

FUNCTION = "pongPlayer_InterpolateCourtGridPosition"
ADDRESS = 0x8219E590
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000


def inputs(t):
    factors = t.alloc(16, "factors")
    a = t.alloc(16, "cornerA")
    b = t.alloc(16, "cornerB")
    offset = t.alloc(16, "offset")
    output = t.alloc(16, "output")
    court = t.alloc(32, "court")
    for ptr in (a, b, offset, output):
        t.floats(ptr, 4, -50, 50)
    for k in range(2):
        t.wf32(factors + k * 4, t.pick([0.0, 1.0, -1.0, t.f32(-2, 2)]))
    # VMX vaddfp flushes denormal operands/results; scalar fadds does not.
    for ptr in (offset, output):
        t.wf32(ptr + 12, t.pick([0.0, -0.0, 1e-40, -1e-40, t.f32(-50, 50)]))
    t.wf32(court + 20, t.f32(-5, 5))
    t.w32(0x8271A304, court)
    # Non-boolean flip values and noisy upper bits exercise clrlwi r4,24.
    flip = t.pick([0, 1, 2, 128, 255]) | (t.u32() & 0xFFFFFF00)
    output = t.pick([output, output, output, offset, a, b])
    t.args(r3=factors, r4=flip, r5=output, r6=a, r7=b, r8=offset)
