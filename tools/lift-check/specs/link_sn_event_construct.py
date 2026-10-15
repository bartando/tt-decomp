"""rage::snEvent constructor (0x823DDA08): vtables, two resource fixups, cleared links."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "snEvent_Construct"
ADDRESS = 0x823DDA08
SOURCE = "src/rage/network/sn_event.cpp"

EXTERNS = {"rage::g_vtbl_hsmEvent": 0x82072864}

CALLS = {
    "datResource_PointerFixup": stub(ret="void", args=("r3",)),
}


def inputs(t):
    ev = t.alloc(0x18, "event")
    t.args(r3=ev)
