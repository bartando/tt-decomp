"""Read before optional wrap shuffle; bit 7 reshuffles, bit 6 makes one-based."""
from liftcheck.spec import *

FUNCTION = 'gmPracticeTargetWordArray_Next'
ADDRESS = 0x821B2C08
SOURCE = 'src/game/match/pong_match.cpp'
TRIALS = 1200
CALLS = {'gmPracticeTargetWordArray_Shuffle': run(args=('r3',))}


def inputs(t):
    r = t.rng
    count = r.randrange(1, 17)
    array = t.alloc(0x20, 'array')
    t.w32(array, t.alloc(count * 4, 'words'))
    t.w32(array + 4, count)
    t.w32(array + 8, count)
    t.w32(array + 12, r.choice([0, count - 1, r.randrange(count)]))
    t.w8(array + 16, r.choice([0, 1, 0x40, 0x80, 0xC0, t.u32()]))
    t.w32(0x825CA2C8, t.u32())
    t.w32(0x825CA2CC, t.u32())
    t.args(r3=array)
