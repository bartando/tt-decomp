"""The empty-list path seeds its score from the image, rather than a guessed -FLT_MAX."""
from liftcheck.spec import *

FUNCTION = "rage::phSimulator::FindWeakestInst"
ADDRESS = 0x822C3800
SOURCE = "src/physics/ph_physics.cpp"


def inputs(t):
    t.wf32(0x8202D108, t.pick([0.0, 1.0, -1.0, 123.25]))
    t.args(r3=t.alloc(4, "sim"), r4=t.alloc(32, "breakable"),
           r5=t.alloc(4, "instances"), r6=t.pick([0, 0xFFFFFFFF]),
           r7=t.alloc(4, "score"), r9=t.alloc(4, "swapA"), r10=t.alloc(4, "swapB"))
