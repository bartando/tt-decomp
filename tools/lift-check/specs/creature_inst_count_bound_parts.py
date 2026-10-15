"""pongCreatureInst::CountBoundParts (0x822C92D8, slot 37): non-null part
pointers of the archetype's bound."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::CountBoundParts"
ADDRESS = 0x822C92D8
SOURCE = "src/game/creature/pong_creature.cpp"


def inputs(t):
    rng = t.rng
    n = rng.choice([0, 1, 5, 20])
    parts = t.alloc(4 * max(n, 1), "parts")
    for k in range(n):
        t.w32(parts + 4 * k, rng.choice([0, rng.getrandbits(32) | 1]))
    bound = t.alloc(0x90, "bound")
    t.w32(bound + 0x70, parts)
    t.w16(bound + 0x82, n)
    arch = t.alloc(0x10, "archetype")
    t.w32(arch + 0x0C, bound)
    inst = t.alloc(0x130, "inst")
    t.w32(inst + 4, arch)
    t.args(r3=inst)
