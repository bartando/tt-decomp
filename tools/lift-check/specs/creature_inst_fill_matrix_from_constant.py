"""pongCreatureInst::FillMatrixFromConstant (0x822C9200, slot 31): four copies
of the vector at 0x82606750 (zero in the image; random here so the copy shows)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::FillMatrixFromConstant"
ADDRESS = 0x822C9200
SOURCE = "src/game/creature/pong_creature.cpp"


def inputs(t):
    rng = t.rng
    for k in range(4):
        t.w32(0x82606750 + 4 * k, rng.getrandbits(32))
    out = t.alloc(0x40, "outMatrix")
    t.args(r3=t.alloc(0x130, "inst"), r4=out)
