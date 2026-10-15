"""PlaceFaceAnimItemMap (0x820C2A58): atMap rsc constructor, face anim items."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _rage_rsc import externs, Rsc, build_map

FUNCTION = "rage::PlaceFaceAnimItemMap"
ADDRESS = 0x820C2A58
SOURCE = "src/rage/animation/rage_anim.cpp"
EXTERNS = externs(ADDRESS)

CALLS = {
    0x82387530: run(),   # PlaceMapKeyString
    0x820C2BA0: run(),   # PlaceFaceAnimItem
}


def item(rsc):
    it = rsc.place(0x20)
    rsc.wptr(it + 0x18, rsc.maybe(rsc.string()))
    rsc.wptr(it + 0x1C, rsc.maybe(rsc.place(0x10)))
    return rsc.saved(rsc.maybe(it))


def inputs(t):
    rsc = Rsc(t)
    m = build_map(rsc, item)
    t.args(r3=m, r4=rsc.addr, r5=t.rng.getrandbits(32), r6=t.rng.getrandbits(32))
