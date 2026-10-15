"""rage::grmModelFactory::ScalarDtor (0x820F3C50): scalar deleting destructor."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::grmModelFactory::ScalarDtor"
ADDRESS = 0x820F3C50
SOURCE = "src/rage/rage_grm.cpp"

CALLS = {
    "rage_free": stub(ret="void"),
    "grmModelFactory_sm_DeclMap_dtor": stub(ret="void"),
}


def inputs(t):
    obj = t.alloc(0x40, "obj")
    t.args(r3=obj, r4=t.rng.choice([0, 1, 2, 3, t.rng.getrandbits(32)]))
