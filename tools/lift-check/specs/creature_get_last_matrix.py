"""pongCreatureInst::GetLastMatrix: returns this + 0xE0."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::GetLastMatrix"
ADDRESS = 0x820C8ED8
SOURCE = "src/game/creature/pong_creature.cpp"


def inputs(t):
    inst = t.alloc(0x130, "inst")
    t.args(r3=inst)
