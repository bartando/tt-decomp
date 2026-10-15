"""pongTrainingDrill::Init (slot 3, 0x8210CDB8): counters, rank and target reset."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongTrainingDrill::Init"
ADDRESS = 0x8210CDB8
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    t.args(r3=t.alloc(0x40, "drill"))
