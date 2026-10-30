"""0x821C9D68: full OR/AND truth table, including noncanonical booleans."""
from liftcheck.spec import *

FUNCTION = "io_Input_poll_9D68"
ADDRESS = 0x821C9D68
SOURCE = "src/rage/core/io_input.cpp"
TRIALS = 1000


def inputs(t):
    obj = t.alloc(0x160, "inputState")
    bits = t.index % 8
    t.w8(obj + 334, t.pick([1, 2, 128, 255]) if bits & 1 else 0)
    t.w32(obj + 340, t.pick([1, 0x100, 0x80000000, 0xFFFFFFFF]) if bits & 2 else 0)
    t.w8(obj + 332, t.pick([1, 2, 128, 255]) if bits & 4 else 0)
    t.args(r3=obj)
