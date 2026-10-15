"""pongTrainingDrill::IsFinished (slot 7, 0x8210D0E8): over once every try is used."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongTrainingDrill::IsFinished"
ADDRESS = 0x8210D0E8
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    rng = t.rng
    config = t.alloc(0x80, "config")
    drill = t.alloc(0x40, "drill")
    total = rng.randrange(-2, 12)
    t.w32(config + 0x10, total)
    t.w32(config + 0x14, rng.randrange(-2, 12))
    t.w32(drill + 0x04, total + rng.randrange(-2, 3))
    t.w32(drill + 0x08, rng.randrange(-2, 12))
    t.w32(drill + 0x20, config)
    t.args(r3=drill, r4=t.alloc(4, "passed"))
