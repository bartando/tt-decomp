"""Exact device writes and packet words, reserved bits, cursor boundaries and
unrelated state. Packet buffers have guards. Downstream setters and refills are
observed boundary models; no ignored bytes or float tolerance.
"""
from liftcheck.spec import *
from specs._grc_state_helpers_inputs import device, REFILL_CALLS
FUNCTION = "grc_3410"
ADDRESS = 0x82363410
SOURCE = "src/graphics/grc_state_helpers.cpp"
TRIALS = 800
CALLS = REFILL_CALLS

def inputs(t):
    p, _ = device(t)
    t.args(r3=p)
