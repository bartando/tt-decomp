"""pongCreatureInst::ApplyToRope (0x821210A8, slot 11): slot 16, then for a
cached instance whose behaviour casts to rage::phRope, phRope_ApplyAtSegment."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::ApplyToRope"
ADDRESS = 0x821210A8
SOURCE = "src/game/creature/pong_creature.cpp"

# Markers on the comment line above a declaration aren't picked up.
EXTERNS = {
    "phRope_ApplyAtSegment": 0x823458F0,
    "RTDynamicCast": 0x82430978,
}

CALLS = {
    "inst.vfn_16": stub(ret="void", args=("r3", "r4", "r5", "r6")),
    # __RTDynamicCast(obj, 0, &phInstBehavior, &phRope, 0): a rope or null
    0x82430978: stub(ret=lambda ctx: ctx.rng.choice([0, ctx.r(3)]), args=("r3", "r4", "r5", "r6", "r7")),
    0x823458F0: stub(ret="void", args=("r3", "r4", "r5", "r6")),
}


def inputs(t):
    rng = t.rng
    inst = t.alloc(0x130, "inst")
    t.w32(inst, t.vtable("inst", 60))
    if rng.random() < 0.8:
        entry = t.alloc(0x210, "entry")
        t.w32(entry + 0x200, rng.choice([0, t.alloc(0x40, "behavior")]))
    else:
        entry = 0
    t.w32(inst + 0x54, entry)
    vec = t.alloc(0x10, "vec")
    t.floats(vec, 4, -10.0, 10.0)
    point = t.alloc(0x10, "point")
    t.floats(point, 4, -10.0, 10.0)
    t.args(r3=inst, r4=vec, r5=point, r6=rng.randrange(16))
