from liftcheck.spec import *

FUNCTION = "rage::crAnimDofQuaternion::Evaluate"
ADDRESS = 0x820C4BF0
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1000
RET = None
CALLS = {"rage::crAnimEvaluateQuaternionChannels": stub(ret="void", args=("r3", "r4", "r5", "f1"), deref={"r5": 16})}


def inputs(t):
    obj = t.alloc(64, "dof")
    context = t.alloc(32, "context")
    out = t.alloc(16, "output")
    t.args(r3=obj, r4=context, r5=out, f1=t.rng.uniform(-10, 10))
