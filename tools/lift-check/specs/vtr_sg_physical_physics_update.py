"""sgPhysicalObject::PhysicsUpdate (0x823D9368), slot 33: the draw object's slot 5, f1 passed on."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "sgPhysicalObject::PhysicsUpdate"
ADDRESS = 0x823D9368
SOURCE = "src/scene/sg_physical.cpp"

CALLS = {
    "obj.vfn_5": stub(ret="void", args=("r3", "f1")),
}


def inputs(t):
    node = t.alloc(0x80, "node")
    obj = t.alloc(0x90, "drawObj")
    t.w32(obj, t.vtable("obj", slots=9))
    t.w32(node + 0x7C, obj)
    t.args(r3=node, f1=t.rng.uniform(-4, 4))
