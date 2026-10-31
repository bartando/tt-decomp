"""0x820CA390: sign reversal and idle/start latch timers, including equality/NaN.

Cross all state-byte forms with zero, signed-zero, nonzero, unordered input and
both timer thresholds. Mutable delay/dt are varied; every byte is compared.
"""
from liftcheck.spec import *

FUNCTION = "pongMover_UpdateMovementState"
ADDRESS = 0x820CA390
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
EXTERNS = {"g_kTransitionStep": 0x825CAEC0, "g_moverStartDelay": 0x825C9D60,
           "g_moverStopDelay": 0x820290F0}


def inputs(t):
    rng = t.rng
    mover = t.alloc(0x110, "mover with guards") + 16
    t.floats(mover + 0x10, 12, -20, 20)
    dt = rng.choice((0., 0.125, -0.25, 0.5))
    delay = rng.choice((0., -1., 1.75, 2., float('nan')))
    t.wf32(t.sym("g_kTransitionStep"), dt)
    t.wf32(t.sym("g_moverStartDelay"), delay)
    kind = t.index % 12
    pairs = ((0., 0.), (-0., 0.), (0., -0.), (1., 0.), (-1., 0.), (0., 1.),
             (0., -1.), (1., -1.), (float('nan'), 0.), (0., float('nan')),
             (1., 1.), (rng.uniform(-10, 10), rng.uniform(-10, 10)))
    x, z = pairs[kind]
    t.wf32(mover + 0x20, x)
    t.wf32(mover + 0x24, z)
    t.wf32(mover + 0x28, rng.choice((0., -1., 1., float('nan'))))
    t.wf32(mover + 0x2C, rng.choice((0., -1., 1., float('nan'))))
    t.w8(mover + 0x74, rng.choice((0, 1, 128, 255)))
    t.w8(mover + 0x84, rng.randrange(256))
    t.wf32(mover + 0x78, rng.choice((delay - dt, delay - dt - 2**-18,
                                    delay - dt + 2**-18, 0., float('nan'))))
    stop = 0.05000000074505806
    t.wf32(mover + 0x7C, rng.choice((stop - dt, stop - dt - 2**-18,
                                    stop - dt + 2**-18, 0., float('nan'))))
    if t.index < 16:
        # Directed exact comparisons, independent of random branch combinations.
        t.wf32(t.sym("g_kTransitionStep"), 0.)
        t.wf32(t.sym("g_moverStartDelay"), 1.75)
        t.wf32(mover + 0x20, 0. if t.index < 8 else 1.)
        t.wf32(mover + 0x24, 0.)
        t.wf32(mover + 0x28, 1.)
        t.wf32(mover + 0x2C, 0.)
        t.w8(mover + 0x74, 0 if t.index < 8 else 1)
        t.w8(mover + 0x84, 255)
        edge = (0., -2**-18, 2**-18, float('nan'))[t.index % 4]
        t.wf32(mover + 0x7C, stop + edge)
        t.wf32(mover + 0x78, 1.75 + edge)
    t.args(r3=mover)
