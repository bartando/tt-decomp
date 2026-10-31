"""Forward non-self swaps; n<=2 consumes no randomness, cursor always resets."""
from liftcheck.spec import *

FUNCTION = 'gmPracticeTargetWordArray_Shuffle'
ADDRESS = 0x821B2B28
SOURCE = 'src/game/match/pong_match.cpp'
TRIALS = 1200


def inputs(t):
    r = t.rng
    capacity = r.randrange(2, 25)
    array = t.alloc(0x20, 'array')
    t.w32(array, t.alloc(capacity * 4, 'words'))
    t.w32(array + 4, r.choice([-1, 0, 1, 2, capacity]))
    t.w32(array + 8, capacity)
    t.w32(array + 12, t.u32())
    t.w32(0x825CA2C8, t.u32())
    t.w32(0x825CA2CC, t.u32())
    t.args(r3=array)
