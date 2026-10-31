"""Char copy: empty/null ranges, arbitrary bytes, lengths around copy boundaries.
Valid nonempty ranges are disjoint, as required by memcpy. Compare exact end
pointer, copied data, source and guards; execute the original memcpy model.
"""
from liftcheck.spec import *
FUNCTION = "game_DD78_h"
ADDRESS = 0x8222DD78
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"
TRIALS = 800

def inputs(t):
    rng = t.rng
    count = rng.choice([0, 1, 2, 3, 15, 16, 17, 31, 32, 63, 64, 127, rng.randrange(512)])
    first = t.alloc(count + 64, "sourceAndGuards") + rng.randrange(16, 32)
    dest = t.alloc(count + 64, "destinationAndGuards") + rng.randrange(16, 32)
    if not count and rng.randrange(2): first = dest = 0
    t.args(r3=first, r4=first + count, r5=dest)
