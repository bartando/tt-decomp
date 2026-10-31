"""0x820CB598: flag override and stored weight, all flag combinations, exact FP."""
from liftcheck.spec import *

FUNCTION = "pongMover_GetBlendWeight"
ADDRESS = 0x820CB598
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 512


def inputs(t):
    mover = t.alloc(0x110, "mover with guards") + 16
    t.w8(mover + 0x40, t.index % 256)
    t.w32(mover + 0x1C, t.rng.choice((0, 0x80000000, 0x3F000000, 0xBF800000,
                                      0x40000000, 0x7FC12345, t.rng.getrandbits(32))))
    t.args(r3=mover)
