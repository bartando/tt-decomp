"""phUpdateObject::ReleaseFrame (0x8227DA08), slot 0: slot 6 on the current frame slot."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "phUpdateObject::ReleaseFrame"
ADDRESS = 0x8227DA08
SOURCE = "src/physics/ph_update_object.cpp"

EXTERNS = {"g_phFrameIndex": 0x825C4898}

CALLS = {
    "obj.vfn_6": stub(ret="void", args=("r3", "r4", "r5")),
}


def inputs(t):
    obj = t.alloc(0x90, "obj")
    t.w32(obj, t.vtable("obj", slots=9))
    t.w32(obj + 0x14, 0 if t.rng.random() < 0.3 else t.rng.getrandbits(32))
    t.w32(0x825C4898, t.rng.randrange(0, 4))
    t.args(r3=obj, r4=t.rng.getrandbits(32))
