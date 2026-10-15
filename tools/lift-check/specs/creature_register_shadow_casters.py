"""pongCreature::RegisterShadowCasters (vtable 0x82027B08 slot 5).

`this` is the phUpdateObject base (creature + 0x10). The snapshot comes from
this + (0x825C4898's counter + 50) * 4, the atlas from 0x82606350.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::RegisterShadowCasters"
ADDRESS = 0x820C60C8
SOURCE = "src/game/creature/pong_creature.cpp"

# Compare every argument register the asm sets up (the lift once declared
# both callees with the wrong arity).
CALLS = {
    0x8225C668: stub(ret="void", args=("r3", "r4", "r5")),
    0x8213EC70: stub(ret="void", args=("r3", "r4", "r5", "r6", "r7")),
}


def inputs(t):
    rng = t.rng
    idx = rng.randrange(50)
    base = t.alloc(0x200, "updateBase")
    t.w32(base + (idx + 50) * 4, rng.choice([0, t.alloc(0x40, "snapshot")]))
    t.w32(0x825C4898, idx)
    t.w32(0x82606350, rng.getrandbits(32))

    sub = t.alloc(0x50, "sub")
    t.w32(sub + 0x04, rng.getrandbits(32))
    t.w32(sub + 0x40, rng.choice([0, t.alloc(0x10, "emitter0")]))
    t.w32(sub + 0x48, rng.choice([0, t.alloc(0x10, "emitter1")]))
    ch = t.alloc(0x20, "char")
    t.w32(ch + 0x14, sub)
    t.w32(base + 0x90, ch)
    t.args(r3=base, r4=rng.choice([0, 1]))
