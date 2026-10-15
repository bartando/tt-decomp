"""pongCreatureInst::PrepareForActivation (0x820C8F80, slot 30): runs
fragInst's slot 30 (0x82120120) with the same arguments, returns null."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::PrepareForActivation"
ADDRESS = 0x820C8F80
SOURCE = "src/game/creature/pong_creature.cpp"

EXTERNS = {"fragInst_PrepareForActivation": 0x82120120}   # marker on the line above

CALLS = {
    0x82120120: stub(args=("r3", "r4", "r5", "r6", "r7")),
}


def inputs(t):
    rng = t.rng
    inst = t.alloc(0x130, "inst")
    out = t.alloc(4, "outObject")
    t.args(r3=inst, r4=out, r5=rng.choice([0, rng.getrandbits(32)]),
           r6=rng.choice([0, rng.getrandbits(32)]), r7=rng.choice([0, rng.getrandbits(32)]))
