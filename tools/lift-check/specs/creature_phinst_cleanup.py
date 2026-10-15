"""pongCreatureInst_Cleanup (0x822C8FD0, rage::phInst's destructor body):
phInst vtable, release the archetype through 0x822C9D98, datBase vtable."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst_Cleanup"
ADDRESS = 0x822C8FD0
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    0x822C9D98: stub(args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    inst = t.alloc(0x130, "inst")
    t.w32(inst + 4, rng.choice([0, t.alloc(0x20, "archetype")]))
    t.args(r3=inst)
