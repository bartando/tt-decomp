"""0x820C0170 (phJoint3Dof_0170_g): the vector constructor iterator, ctor(p) for count elements of stride bytes."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "phJoint3Dof_0170_g"
ADDRESS = 0x820C0170
SOURCE = "src/physics/ph_update_object.cpp"

CALLS = {"ctor": stub(ret="void")}


def inputs(t):
    n = t.rng.choice([0, 1, 4])
    stride = t.rng.choice([16, 64, 144])
    t.args(r3=t.alloc(stride * max(n, 1), "array"), r4=stride, r5=n, r6=t.fake_fn("ctor"))
