"""0x8223ACB0: projected four-lane correction, exact thresholds and input aliasing."""
from liftcheck.spec import *
FUNCTION = 'phVector_AccumulateProjected'
ADDRESS = 0x8223ACB0
SOURCE = 'src/physics/collider_velocity.cpp'
TRIALS = 600
FTOL = 1e-99
FP_CONTRACT = 'off'
EXTERNS = {'g_floatOne': 0x8202D108, 'g_floatZero': 0x8202D110}


def inputs(t):
    current = t.alloc(48, 'currentAndGuards') + 16
    delta = t.alloc(48, 'deltaAndGuards') + 16
    t.floats(current, 4, -10, 10)
    t.floats(delta, 4, -10, 10)
    if t.index % 4 == 0:
        for i in range(3):
            t.wf32(current + i * 4, t.pick((-2., -1., 0., 1., 2.)) if i == 0 else 0.)
            t.wf32(delta + i * 4, 1. if i == 0 else 0.)
    if t.index % 5 == 0:
        delta = current
    if t.index % 7 == 0:
        t.w32(t.pick((current, delta)) + 4 * t.rng.randrange(4), t.pick((1, 0x807fffff,
              0x7f800000, 0xff800000, 0x7fc00000, 0x80000000)))
    if t.index % 19 == 1:
        t.wf32(delta, float('nan'))
    t.args(r3=current, r4=delta)
