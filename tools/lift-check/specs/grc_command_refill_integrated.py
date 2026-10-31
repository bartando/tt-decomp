"""Refill runs the original query, append and finalize bodies on both sides.
Allocation, OS locks and lower GPU submission helpers remain explicit boundaries."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from _grc_command_helpers_inputs import inputs as common, CALLS as boundaries, HOST
from liftcheck.spec import run
FUNCTION = 'rage_A980'
ADDRESS = 0x8235A980
SOURCE = 'src/graphics/grc_command_stream.cpp'
TRIALS = 600
CALLS = dict(boundaries)
CALLS.update({'rage_A4E0': run(), 'rage_A8C0': run(), 'rage_A780': run()})


def inputs(t):
    common(t, 'finalize')
    t.w32(0x8260663C, 0)  # Per-thread handle retirement has its own full spec.
