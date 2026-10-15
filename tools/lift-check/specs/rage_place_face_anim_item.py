"""PlaceFaceAnimItem (0x820C2BA0): relocates an item pointer, then the item's two pointers."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _rage_rsc import externs, Rsc

FUNCTION = "rage::PlaceFaceAnimItem"
ADDRESS = 0x820C2BA0
SOURCE = "src/rage/animation/rage_anim.cpp"
EXTERNS = externs(ADDRESS)


def inputs(t):
    rsc = Rsc(t)
    it = rsc.place(0x20)
    rsc.wptr(it + 0x18, rsc.maybe(rsc.string()))
    rsc.wptr(it + 0x1C, rsc.maybe(rsc.place(0x10)))
    slot = t.alloc(4, "slot")
    rsc.wptr(slot, rsc.maybe(it))
    t.args(r3=rsc.addr, r4=slot)
