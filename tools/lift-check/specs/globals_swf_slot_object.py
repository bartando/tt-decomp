"""Slot-13 mode uses 0x82604848, distinct from the script globals at 0x82602818."""
from liftcheck.spec import *

FUNCTION = "rage::swfContext_IsGlobalSlot13AltMode"
ADDRESS = 0x823FB1F0
SOURCE = "src/rage/swf.cpp"


def slot(ctx):
    ctx.ret(r3=ctx.r(3) + 8)


CALLS = {0x823FB188: model(slot, args=("r3", "r4"))}


def inputs(t):
    t.w32(0x82604848, t.alloc(16, "slotObject"))
    t.w32(0x82602818, t.alloc(16, "scriptGlobals"))
    t.args()
