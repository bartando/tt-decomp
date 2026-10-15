"""pongCreature::RefreshBallSlot: copies the ball's instance into the cell at
+0x160 and asks the physics level (0x825F5BD0 -> +4) for its active body."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::RefreshBallSlot"
ADDRESS = 0x820C58B8
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    "level.vfn_4": stub(ret=lambda ctx: ctx.rng.choice([0, 0x40001000]), args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    creature = t.alloc(0x170, "creature")
    sk = t.alloc(0x20, "obj24.data")
    t.w32(sk + 0x14, rng.getrandbits(32))
    obj24 = t.alloc(0x10, "obj24")
    t.w32(obj24 + 4, sk)
    t.w32(creature + 0x24, obj24)
    t.w32(creature + 0x160, t.alloc(0x10, "ballSlot"))

    level = t.alloc(0x40, "level")
    t.w32(level, t.vtable("level", 16))
    states = t.alloc(0x40, "objectStates")
    for k in range(0x40):
        t.w8(states + k, rng.choice([0, 0, 8, 1, 5]))
    t.w32(level + 0x1C, states)
    sim = t.alloc(0x10, "sim")
    t.w32(sim + 4, level)
    t.w32(0x825F5BD0, sim)

    if rng.random() < 0.85:
        ball = t.alloc(0x10, "ballInst")
        t.w16(ball + 8, rng.randrange(0x40))
    else:
        ball = 0
    cell = t.alloc(4, "ballCell")
    t.w32(cell, ball)
    t.w32(0x8271A2F4, cell)
    t.args(r3=creature, r4=rng.getrandbits(32), r5=rng.getrandbits(32))
