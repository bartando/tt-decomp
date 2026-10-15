"""pongCreatureInst::ApplyAtPosition (0x822C90B0): rage::phInst's, tail-calls vtable slot 10."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::ApplyAtPosition"
ADDRESS = 0x822C90B0
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    "inst.vfn_10": stub(ret="void", args=("r3", "r4", "r5", "r6", "r7")),
}


def inputs(t):
    rng = t.rng
    inst = t.alloc(0x130, "inst")
    t.w32(inst, t.vtable("inst", 60))
    vec = t.alloc(0x10, "vec")
    t.floats(vec, 4, -10.0, 10.0)
    point = t.alloc(0x10, "point")
    t.floats(point, 4, -10.0, 10.0)
    t.args(r3=inst, r4=vec)
