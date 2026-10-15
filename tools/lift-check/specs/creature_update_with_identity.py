"""pongCreature::UpdateWithIdentity (0x820C6358, vtable 0x82027B08 slot 0; was
lifted as ~pongCreature): tail-calls the object's own slot 6 with
(this, 0x825CB800, caller's r4)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::UpdateWithIdentity"
ADDRESS = 0x820C6358
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    "obj.vfn_6": stub(ret="void", args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    base = t.alloc(0x100, "updateBase")
    t.w32(base, t.vtable("obj", 16))
    t.args(r3=base, r4=rng.getrandbits(32))
