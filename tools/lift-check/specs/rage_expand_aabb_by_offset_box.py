"""0x82143F08: merge a nonempty center/full-size/offset box into an AABB.

The merge helper is a stub boundary: verify call presence, destination pointer
and its existing 32 bytes, all four center+offset lanes and all four size lanes
before it writes a scripted result.
Cover xyz-only emptiness mask, w-only data, signed zero, denormals, NaN/inf,
negative/full sizes, and aliased boxes. FTOL=0, no ignored memory. This proves
the wrapper, not the merge callee, FP flags, or NaN payload selection.
"""
from liftcheck.spec import *

FUNCTION = "rage::expandAabbByOffsetBox"
ADDRESS = 0x82143F08
SOURCE = "src/rage/math/polygon_clip.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


CALLS = {0x82143F90: stub(ret="void", args=("r3", "r4", "r5"),
                          deref={"r3": 32, "r4": 16, "r5": 16}, out={"r3": 32})}


def inputs(t):
    rng = t.rng
    storage = t.alloc(192, "boxesAndGuards")
    box = storage + 64
    destination = box + rng.choice((-48, -16, 0, 16, 48))
    t.floats(destination, 12, -10, 10)
    t.floats(box, 12, -10, 10)
    kind = rng.randrange(10)
    size = [rng.uniform(-5, 5) for _ in range(4)]
    if kind < 3:
        size[:3] = [rng.choice((0., -0., 2.**-149, -2.**-140)) for _ in range(3)]
    elif kind < 6:
        size[:3] = [0., 0., 0.]
        size[kind - 3] = rng.choice((1., -1., 2.**-126, float("nan"), float("inf")))
    elif kind == 6:
        size[:3] = [0., 0., 0.]
        size[3] = float("nan")
    if kind >= 7:
        for vector in (0, 2):
            for lane in range(4):
                t.wf32(box + vector * 16 + lane * 4,
                       rng.choice((2.**-149, -2.**-140, 2.**-126, rng.uniform(-10, 10))))
    for lane, value in enumerate(size):
        t.wf32(box + 16 + lane * 4, value)
    t.args(r3=destination, r4=box)
