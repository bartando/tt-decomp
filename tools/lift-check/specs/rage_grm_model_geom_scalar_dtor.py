"""rage::grmModelGeom::ScalarDtor (0x820F0EE8): scalar deleting destructor."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::grmModelGeom::ScalarDtor"
ADDRESS = 0x820F0EE8
SOURCE = "src/rage/rage_grm.cpp"

CALLS = {
    "rage_free": stub(ret="void"),
    "rage_0F38": stub(ret="void"),
}


def inputs(t):
    obj = t.alloc(0x40, "obj")
    t.args(r3=obj, r4=t.rng.choice([0, 1, 2, 3, t.rng.getrandbits(32)]))
