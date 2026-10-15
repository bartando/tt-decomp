"""phUpdateObject::Destroy (0x820C41E8), slot 2: scalar deleting destructor."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "phUpdateObject::Destroy"
ADDRESS = 0x820C41E8
SOURCE = "src/physics/ph_update_object.cpp"

CALLS = {
    "phDemoObject_Dtor": stub(ret="void"),
    "rage_free": stub(ret="void"),
}


def inputs(t):
    obj = t.alloc(0x90, "obj")
    t.args(r3=obj, r4=t.rng.choice([0, 1, 2, 3, t.rng.getrandbits(32)]))
