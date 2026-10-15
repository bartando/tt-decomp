"""PlaceObservedMap (0x820CFA40): atMap rsc constructor, data placed by PlaceAnimObservedPtr."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _rage_rsc import externs, Rsc, build_map

FUNCTION = "rage::PlaceObservedMap"
ADDRESS = 0x820CFA40
SOURCE = "src/rage/animation/rage_anim.cpp"
EXTERNS = externs(ADDRESS)

CALLS = {
    0x82387530: run(),               # PlaceMapKeyString
    0x820CF728: stub(ret="void"),    # PlaceAnimObservedPtr (runs pcrAnimObserved's rsc ctor)
}


def inputs(t):
    rsc = Rsc(t)
    m = build_map(rsc, lambda r: r.saved(r.maybe(r.place(0x40))))
    t.args(r3=m, r4=rsc.addr, r5=t.rng.getrandbits(32), r6=t.rng.getrandbits(32))
