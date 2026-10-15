"""pongCreatureInst::ScalarDeletingDtor (0x820C8EE0, slot 0): destroys the
bound atArray (vector deleting dtor with flags 3, or frees an empty block),
runs fragInst's destructor body, frees this when bit 0 of flags is set."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::ScalarDeletingDtor"
ADDRESS = 0x820C8EE0
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    "bounds.vfn_0": stub(args=("r3", "r4")),
    0x8211D470: stub(ret="void"),        # FragInstDtor (own spec)
    0x820C00C0: stub(ret="void"),        # rage_free
}


def inputs(t):
    rng = t.rng
    inst = t.alloc(0x130, "inst")
    block = t.alloc(0x10 + 0x100 * 2, "boundsBlock")
    t.w32(block, rng.choice([0, 2]))                      # element count cookie
    bounds = block + 0x10
    t.w32(bounds, t.vtable("bounds", 4))
    t.w32(inst + 0x124, rng.choice([bounds, bounds, 0]))
    t.w16(inst + 0x12A, rng.choice([0, 2, 2]))
    t.args(r3=inst, r4=rng.choice([0, 1, 2, 3]))
