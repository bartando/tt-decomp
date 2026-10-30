from liftcheck.spec import *

FUNCTION = "rage::crAnimDofVector3::Normalize"
ADDRESS = 0x820C4AF8
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1000
RET = None

def inputs(t):
    obj = t.alloc(48, "vector and guards")
    for i in range(3):
        t.w32(obj + 16 + i * 4, t.rng.choice([0, 0x80000000, 0x7fc00001, t.u32()]))
    t.args(r3=obj)
