"""sgPhysicalObject::AdvancedPhysics (0x823D98C0), slot 39: builds the draw object at +0x7C."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "sgPhysicalObject::AdvancedPhysics"
ADDRESS = 0x823D98C0
SOURCE = "src/scene/sg_physical.cpp"

EXTERNS = {"g_physicsSystem": 0x82606568}

CALLS = {
    "CreatePhysicsInstance": stub(),
    "CreateSimplePhysicsInstance": stub(),
    "LinkPhysicsResource": stub(ret="void"),
}


def inputs(t):
    node = t.alloc(0x80, "node")
    t.w8(node + 0x72, t.rng.choice([0, 1]))
    t.w32(node + 0x74, t.alloc(0x10, "physType"))
    t.w32(0x82606568, t.rng.getrandbits(32))
    t.args(r3=node)
