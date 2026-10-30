"""0x823D8CD0: return embedded vector address; no loads, stores or calls.

Random object contents and byte offsets catch accidental dereferencing,
alignment masking, copying, initialization, and returning a different lane.
Pointer return and the entire input allocation are compared exactly.
"""
from liftcheck.spec import *

FUNCTION = "rage::crAnimDofVector3::GetVector"
ADDRESS = 0x823D8CD0
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1200
FTOL = 0


def inputs(t):
    dof = t.alloc(96, "dofAndGuards") + 16 + t.index % 16
    t.args(r3=dof)
