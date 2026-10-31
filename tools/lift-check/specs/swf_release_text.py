"""Release finite chunk chains tail-first; compare the entire free-list state.

Flags vary across all bits and are ignored by retail. Counts include wrapping.
"""
from liftcheck.spec import *

FUNCTION = "swfReleaseText"
ADDRESS = 0x823F8A38
SOURCE = "src/rage/swf_text.cpp"
TRIALS = 400
CALLS = {ADDRESS: run()}


def inputs(t):
    rng = t.rng
    pool = t.alloc(20, "pool")
    free = t.alloc(16, "existingFree") if rng.randrange(2) else 0
    t.w32(pool + 12, free)
    t.w16(pool + 6, rng.choice((0, 1, 0xfffe, 0xffff, rng.randrange(65536))))
    t.w32(0x82602844, pool)  # g_swfTextPool
    head = 0
    for _ in range(rng.choice((1, 2, 3, 8, 32))):
        node = t.alloc(16, "textChunk")
        t.w32(node + 12, head)
        head = node
    t.args(r3=head, r4=rng.getrandbits(32))
