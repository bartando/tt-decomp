"""Forward CRT copy: overlapping and disjoint buffers, alignments and boundary sizes."""
from liftcheck.spec import *

FUNCTION = "crtBlkmov"
ADDRESS = 0x82434520
SOURCE = "src/crt/memory.c"
TRIALS = 1000
EXTRA_RANGES = [(0x82434548, 0x824345c8)]


def inputs(t):
    r = t.rng
    src = t.alloc(320, 'source') + r.randrange(4)
    if r.randrange(3) == 0:
        dst = src + r.choice([-3, -2, -1, 0, 1, 2, 3, 4, 8])
        src += 8
        dst += 8
    else:
        dst = t.alloc(320, 'destination') + r.randrange(4)
    size = r.choice([0, 1, 2, 3, 4, 5, 7, 8, 15, 16, 31, 32, 63, 64, 127, 128, r.randrange(256)])
    t.args(r3=dst, r4=src, r5=size)
