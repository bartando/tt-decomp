"""PlaceAnimObserver (0x820CF848): pcrAnimObserver rsc constructor."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _rage_rsc import externs, Rsc

FUNCTION = "rage::PlaceAnimObserver"
ADDRESS = 0x820CF848
SOURCE = "src/rage/animation/rage_anim.cpp"
EXTERNS = externs(ADDRESS)

CALLS = {
    0x820CF778: stub(ret="void"),   # PlaceAnimObserverHash (checked by its own spec)
}


def inputs(t):
    rng = t.rng
    rsc = Rsc(t)
    o = rsc.place(0x14)
    n = rng.choice([0, 1, 2, 4, 7])
    if n or rng.random() < 0.5:
        arr = rsc.place(4 * max(n, 1))
        for i in range(n):
            rsc.wptr(arr + 4 * i, rsc.maybe(rsc.place(0x24), 0.25))
        rsc.wptr(o + 0x0C, arr)
    else:
        t.w32(o + 0x0C, 0)
    rsc.wptr(o + 0x08, rsc.maybe(rsc.place(0x10)))
    t.w16(o + 0x10, n)
    t.args(r3=o, r4=rsc.addr)
