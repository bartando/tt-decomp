"""PlaceCreatureTypeMap (0x820C3700): atMap rsc constructor, data are bare pointers."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _rage_rsc import externs, Rsc, build_map

FUNCTION = "rage::PlaceCreatureTypeMap"
ADDRESS = 0x820C3700
SOURCE = "src/rage/animation/rage_anim.cpp"
EXTERNS = externs(ADDRESS)

CALLS = {
    0x82387530: run(),   # PlaceMapKeyString
}


def inputs(t):
    rsc = Rsc(t)
    m = build_map(rsc, lambda r: r.saved(r.maybe(r.place(0x10))))
    t.args(r3=m, r4=rsc.addr, r5=t.rng.getrandbits(32), r6=t.rng.getrandbits(32))
