"""grmShaderFactoryStandard::vfn_6 (0x820F7290): relocate a grmShaderGroup pointer, rsc-construct it."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _rage_rsc import Rsc

FUNCTION = "rage::grmShaderFactoryStandard::vfn_6"
ADDRESS = 0x820F7290
SOURCE = "src/rage/rage_grm.cpp"

CALLS = {
    "fragDrawable_3010": stub(ret="void"),   # grmShaderGroup rsc constructor
}


def inputs(t):
    rsc = Rsc(t)
    slot = t.alloc(4, "slot")
    rsc.wptr(slot, rsc.maybe(rsc.place(0x40)))
    t.args(r3=t.alloc(0x10, "factory"), r4=rsc.addr, r5=slot)
