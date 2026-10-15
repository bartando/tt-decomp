"""PlaceAnimObserverHash (0x820CF778): pcrAnimObserverHash rsc constructor."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _rage_rsc import externs, Rsc

FUNCTION = "rage::PlaceAnimObserverHash"
ADDRESS = 0x820CF778
SOURCE = "src/rage/animation/rage_anim.cpp"
EXTERNS = externs(ADDRESS)

CALLS = {
    0x820CFA40: stub(ret="void"),   # PlaceObservedMap (checked by its own spec)
    0x820CFB88: run(),              # PlaceXmlRootPtr
    0x820CF0F0: stub(ret="void"),   # pcrAnimObserverHash_BuildTree
}


def inputs(t):
    rsc = Rsc(t)
    h = rsc.place(0x24)
    rsc.wptr(h + 0x04, rsc.maybe(rsc.place(0x20)))
    rsc.wptr(h + 0x20, rsc.maybe(rsc.place(0x10)))
    t.args(r3=h, r4=rsc.addr)
