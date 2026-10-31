"""VMX rows copy bit patterns without arithmetic; exercise forward and backward
partial overlap, self copy, disjoint ranges, multiple matrices and empty/null
ranges. All storage is aligned, and all written bytes and end pointers compare.
Nonempty null destinations (invalid constructed ranges) are out of scope.
"""
from liftcheck.spec import *
FUNCTION = "fiAsciiTokenizer_DDD0_w"
ADDRESS = 0x8222DDD0
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"
TRIALS = 800

def inputs(t):
    rng = t.rng
    count = rng.randrange(9)
    storage = t.alloc(1536, "matrixRangesAndGuards")
    first = storage + 512
    dest = first + rng.choice([-512, -128, -64, -32, -16, 0, 16, 32, 64, 128, 512])
    if not count and rng.randrange(2): first = dest = 0
    t.args(r3=first, r4=first + count * 64, r5=dest)
