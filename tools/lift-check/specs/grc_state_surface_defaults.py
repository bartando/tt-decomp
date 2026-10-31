"""Exact device writes and packet words, reserved bits, cursor boundaries and
unrelated state. Packet buffers have guards. Downstream setters and refills are
observed boundary models; no ignored bytes or float tolerance.
"""
from liftcheck.spec import *
from specs._grc_state_helpers_inputs import device, REFILL_CALLS
FUNCTION = "grc_36E8"
ADDRESS = 0x823536e8
SOURCE = "src/graphics/grc_state_helpers.cpp"
TRIALS = 800
CALLS = {"grcDevice_SetViewport": stub(ret="void", args=("r3", "r4"), deref={"r4": 24})}

def inputs(t):
    p, _ = device(t)
    surface = t.alloc(64, "surface")
    t.w32(surface + 0x30, (t.u32() & ~0x30000) | ((t.index % 4) << 16))
    t.args(r3=p, r4=surface)
