from liftcheck.spec import *

FUNCTION = "rage::crAnimDofVector3::SetValue"
ADDRESS = 0x820C4B10
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1000

def inputs(t):
    obj = t.alloc(64, "vector")
    source = t.alloc(16, "source")
    t.args(r3=obj, r4=source)
