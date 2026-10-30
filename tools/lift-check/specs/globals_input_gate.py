"""Input gate must read the shared 0x825EAB30 slot instead of a private null."""
from liftcheck.spec import *

FUNCTION = "io_ExecuteStateAction"
ADDRESS = 0x822F9E30
SOURCE = "src/rage/core/io_input.cpp"
CALLS = {0x821C9D68: stub(args=("r3",), ret=lambda ctx: ctx.rng.randrange(2))}


def inputs(t):
    gate = t.alloc(580, "gate")
    t.w8(gate + 576, t.pick([0, 1, 255]))
    t.w8(gate + 578, t.pick([0, 1, 255]))
    t.w32(0x825EAB30, gate)
    t.w32(0x825EAB28, t.alloc(0x160, "input"))
    t.args(r3=t.alloc(4, "io"))
