"""Slot 7: sorted depth lookup/insertion, pool bookkeeping and frame reset.

The constructor is modeled: it returns the supplied pool block and clears its
frame, but its other initialization is outside this spec. Pool exhaustion is
excluded: the original dereferences the free-list head before its null check.
Lists are sorted, acyclic and use unique 16-bit depths, as required by lookup.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfINSTANCE::FindOrCreateChildByDepth"
ADDRESS = 0x823FC908
SOURCE = "src/rage/swf.cpp"
TRIALS = 600
EXTERNS = {"g_swfInstancePool": 0x82604C50, "rage_DebugLog": 0x8240E6D0}


def construct(ctx):
    child = ctx.r(3)
    ctx.write(child + 164, b"\0\0")
    ctx.ret(r3=child)


CALLS = {
    0x823FB570: model(construct, args=("r3",), preserves=("r4", "r5", "r6")),
    0x8240E6D0: stub(ret="void", args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    parent = t.alloc(0xD4, "parent")
    pool = t.alloc(16, "pool")
    free = t.alloc(0xD4, "freeChild")
    successor = t.alloc(0xD4, "nextFree")
    t.w32(0x82604C50, pool)
    t.w16(pool + 6, rng.choice((0, 1, 0xffff, rng.randrange(65536))))
    t.w32(pool + 12, free)
    t.w32(free, successor)

    depths = sorted(rng.sample(range(0, 65536), rng.randrange(5)))
    head = 0
    for depth in reversed(depths):
        child = t.alloc(0xD4, "child")
        t.w16(child + 164, rng.choice((0, 1, 2, 65535, rng.randrange(65536))))
        t.w16(child + 166, depth)
        t.w32(child + 184, head)
        head = child
    t.w32(parent + 180, head)
    key = rng.choice(depths) if depths and rng.randrange(2) else rng.randrange(65536)
    # Exercise truncation of both arguments and both sides of the frame boundary.
    definition = t.alloc(12, "definition")
    t.w8(definition + 4, rng.choice((0, 1, 2, 3, 255)))
    t.w16(definition + 8, rng.choice((0, 1, 2, 65535, rng.randrange(65536))))
    t.args(r3=parent, r4=key | (rng.randrange(65536) << 16),
           r5=rng.getrandbits(32), r6=rng.choice((0, definition)))
