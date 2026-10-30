"""crAnimDofVector3::Evaluate thunk: channels from r5, output at this + 0x10."""
from liftcheck.spec import *

FUNCTION = "rage::crAnimDofVector3::Evaluate"
ADDRESS = 0x820C47A0
SOURCE = "src/rage/animation/rage_anim.cpp"
CALLS = {0x820C43D0: stub(ret="void", args=("r3", "r4", "r5", "f1"))}
RET = None


def inputs(t):
    dof = t.alloc(0x20, "dof")
    channels = t.alloc(0x10, "channels")
    t.args(r3=dof, r4=t.u32(), r5=channels, f1=t.rng.uniform(-10, 100))
