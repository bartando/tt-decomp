"""Exact device writes and packet words, reserved bits, cursor boundaries and
unrelated state. Packet buffers have guards. Downstream setters and refills are
observed boundary models; no ignored bytes or float tolerance.
"""
from liftcheck.spec import *
from specs._grc_state_helpers_inputs import device, REFILL_CALLS
FUNCTION = "rage_6858"
ADDRESS = 0x82356858
SOURCE = "src/graphics/grc_state_helpers.cpp"
TRIALS = 800
CALLS = REFILL_CALLS

def inputs(t):
    p, cursor = device(t)
    index = t.index % 6
    plane = t.rng.choice([t.alloc(32, "plane"), p + 0x3230 + index * 16,
                          p + 0x3234 + index * 16, cursor + 4])
    for lane in range(4):
        t.wf32(plane + lane * 4, t.rng.choice([0., -0., 2.**-140, -2.**-140, t.rng.uniform(-100, 100)]))
    t.args(r3=p, r4=index, r5=plane)
