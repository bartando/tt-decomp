from liftcheck.spec import *

FUNCTION = "rage::crAnimDofQuaternion::Normalize"
ADDRESS = 0x820C52B0
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1000

def inputs(t):
    obj = t.alloc(64, "quaternion")
    t.args(r3=obj)
