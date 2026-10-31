"""0x8223AB00: preserve x/w and rotate y/z using rounded sine products and FMA."""
import math
from liftcheck.spec import *

FUNCTION = "phBoundCapsule_RotateAxisXZ"
ADDRESS = 0x8223AB00
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
CALLS = {
    0x824301D8: model(lambda c: c.ret(f1=math.sin(c.f(1))), args=("f1",)),
    0x824302B0: model(lambda c: c.ret(f1=math.cos(c.f(1))), args=("f1",)),
}


def inputs(t):
    vector = t.alloc(16, "axis", floats=[(0, 4)])
    t.floats(vector, 4, -20, 20)
    angle = t.rng.choice([0, 1, -1, 1.5707963705062866, t.rng.uniform(-7, 7)])
    t.args(r3=vector, f1=angle)
