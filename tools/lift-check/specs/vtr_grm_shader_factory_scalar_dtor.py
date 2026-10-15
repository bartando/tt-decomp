"""rage::grmShaderFactory::ScalarDtor (0x820F6E60): scalar deleting destructor."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::grmShaderFactory::ScalarDtor"
ADDRESS = 0x820F6E60
SOURCE = "src/rage/rage_grm.cpp"

CALLS = {
    "rage_free": stub(ret="void"),
}


def inputs(t):
    obj = t.alloc(0x20, "obj")
    t.w32(0x82606374, obj if t.rng.random() < 0.5 else t.rng.getrandbits(32))
    t.args(r3=obj, r4=t.rng.choice([0, 1, 2, 3, t.rng.getrandbits(32)]))
