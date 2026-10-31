"""Exact assigned ranges, retained dispatch/padding, and forward overlap.

Objects have four-byte alignment, including overlapping destinations.
"""
from liftcheck.spec import *

FUNCTION = "swfCopyActionFunction"
ADDRESS = 0x82402FC0
SOURCE = "src/rage/swf_action_copy.cpp"
TRIALS = 300


def inputs(t):
    mode = t.index % 5
    if mode == 0:
        source = t.alloc(0x1CA8, "source")
        destination = t.alloc(0x1CA8, "destination")
    else:
        allocation = t.alloc(0x4000, "overlap")
        delta = t.rng.choice((4, 8, 0x80, 0x400, 0x804))
        if mode == 1:
            source = destination = allocation
        elif mode == 2:
            source, destination = allocation, allocation + delta
        else:
            source, destination = allocation + delta, allocation
    t.args(r3=destination, r4=source)
