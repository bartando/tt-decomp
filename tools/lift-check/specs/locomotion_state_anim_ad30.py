"""Quaternion-to-matrix conversion at 0x8223AD30.

Exercise identity, axis rotations, arbitrary and non-unit quaternions, signed
zeros, small values, and float-aligned input/output overlaps. The whole buffer
is compared, including the three untouched matrix padding words.
Limits: readable float-aligned buffers, default FP rounding, no FPSCR exception
flags or NaN payload/sign comparisons; no infinities or NaNs as inputs. Finite
outputs are compared bit for bit, with no ignored writes.
"""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_AD30_g"
ADDRESS = 0x8223AD30
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 2000
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    block = t.alloc(160, "buffers")
    src = block + 48
    case = rng.randrange(5)
    if case == 0:
        values = [0.0] * 4
        values[rng.randrange(4)] = rng.choice([1.0, -1.0])
    elif case == 1:
        values = [rng.choice([0.0, -0.0, 1.0, -1.0, 0.5, -0.5]) for _ in range(4)]
    elif case == 2:
        values = [rng.uniform(-1e-20, 1e-20) for _ in range(4)]
    else:
        values = [rng.uniform(-10, 10) for _ in range(4)]
    for i, value in enumerate(values):
        t.wf32(src + 4 * i, value)
    dst = src + rng.choice([-40, -24, -12, -4, 0, 4, 8, 12, 16, 32, 48])
    # Compare all words as raw bits, including signed zero and untouched bytes.
    t.float_words.clear()
    t.args(r3=dst, r4=src)
