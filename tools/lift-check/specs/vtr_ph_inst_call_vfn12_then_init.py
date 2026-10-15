"""rage::phInst::CallVfn12ThenInit (0x8248D7C8): slot 12, then 0x82494130 on this."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::phInst::CallVfn12ThenInit"
ADDRESS = 0x8248D7C8
SOURCE = "src/physics/ph_physics.cpp"

CALLS = {
    "inst.vfn_12": stub(ret="void"),
    "statePreInit_vfn_6": stub(ret="void"),
}


def inputs(t):
    obj = t.alloc(0x40, "inst")
    t.w32(obj, t.vtable("inst", slots=49))
    t.args(r3=obj)
