"""Exact device writes and packet words, reserved bits, cursor boundaries and
unrelated state. Packet buffers have guards. Downstream setters and refills are
observed boundary models; no ignored bytes or float tolerance.
"""
from liftcheck.spec import *
from specs._grc_state_helpers_inputs import device, REFILL_CALLS
FUNCTION = "grc_5E08"
ADDRESS = 0x82355e08
SOURCE = "src/graphics/grc_state_helpers.cpp"
TRIALS = 800
CALLS = {"grcDevice_SetScissorRect": stub(ret="void", args=("r3", "r4", "r5", "r6", "r7"))}

def inputs(t):
    p, _ = device(t)
    rect = t.rng.choice([t.alloc(32, "rect"), p + 0x3208, p + 0x3210, p + 0x3220, p + 0x3224])
    t.w32(p + 0x2EB0, t.rng.choice([0, 1, 2, 0xffffffff]))
    for address in [rect + i * 4 for i in range(4)] + [p + 0x3208 + i * 4 for i in range(4)]:
        t.w32(address, t.rng.choice([0, 1, 0xffffffff, 0x80000000, 0x7fffffff, t.u32()]))
    t.args(r3=p, r4=rect)
