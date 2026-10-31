"""0x820C1910: cyclic envelope, zero-phase substitution and unordered branches."""
from liftcheck.spec import *

FUNCTION = 'LocomotionStateAnim::CalculateBlendFactor'
ADDRESS = 0x820C1910
SOURCE = 'src/anim/animation_timing.cpp'
TRIALS = 1200
EXTERNS = {'g_floatOne': 0x8202D108, 'g_floatZero': 0x8202D110}
FP_CONTRACT = 'off'


def inputs(t):
    rng = t.rng
    data = t.alloc(0x20, 'timing and guards')
    edges = (0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x3F800000,
             0x3F7FFFFF, 0x3F800001, 0xBF800000, 0x3E800000,
             0x7FC12345, 0x7F800000, 0xFF800000)
    for offset in (8, 12, 20):
        t.wf32(data + offset, rng.uniform(-2, 2))
        if t.index % 3:
            t.w32(data + offset, rng.choice(edges))
    if t.index % 7 == 0:
        # Continuous envelope borders, including zero widths.
        a, b = rng.choice((0., .125, .25, .5, 1.)), rng.choice((0., .125, .25, .5, 1.))
        t.wf32(data + 8, a)
        t.wf32(data + 12, b)
        t.wf32(data + 20, rng.choice((0., 1., a, 1.-b)))
    t.args(r3=rng.getrandbits(32), r4=data)
