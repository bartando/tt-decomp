"""Exact device writes and packet words, reserved bits, cursor boundaries and
unrelated state. Packet buffers have guards. Downstream setters and refills are
observed boundary models; no ignored bytes or float tolerance.
"""
from liftcheck.spec import *
from specs._grc_state_helpers_inputs import device, REFILL_CALLS
FUNCTION = "grc_DBF8"
ADDRESS = 0x8235dbf8
SOURCE = "src/graphics/grc_state_helpers.cpp"
TRIALS = 800
def inputs(t):
    p, cursor = device(t)
    t.args(r3=p, r4=cursor)
