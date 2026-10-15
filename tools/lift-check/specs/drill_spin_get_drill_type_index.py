"""pongDrillSpin::GetDrillTypeIndex (slot 17, 0x8210CCE0)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillSpin::GetDrillTypeIndex"
ADDRESS = 0x8210CCE0
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    t.args(r3=t.alloc(0x60, "drill"))
