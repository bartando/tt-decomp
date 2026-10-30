from liftcheck.spec import *

FUNCTION = "rage::crAnimDofQuaternion::Evaluate"
ADDRESS = 0x820C4BF0
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1000
RET = None
EXTERNS = {"crAnimDof_BlendQuaternion": 0x820C44A0}
CALLS = {"crAnimDof_BlendQuaternion": stub(ret="void", args=("r3", "r4", "r5"), deref={"r5": 16})}


def inputs(t):
    obj = t.alloc(64, "dof")
    context = t.alloc(32, "context")
    out = t.alloc(16, "output")
    t.args(r3=obj, r4=context, r5=out)
