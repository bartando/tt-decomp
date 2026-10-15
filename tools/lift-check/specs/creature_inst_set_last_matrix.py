"""pongCreatureInst::SetLastMatrix (0x820C8E98, slot 3): copies a 4x4 into +0xE0."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::SetLastMatrix"
ADDRESS = 0x820C8E98
SOURCE = "src/game/creature/pong_creature.cpp"


def inputs(t):
    inst = t.alloc(0x130, "inst")
    m = t.alloc(0x40, "matrix")
    t.floats(m, 16, -10.0, 10.0)
    t.args(r3=inst, r4=m)
