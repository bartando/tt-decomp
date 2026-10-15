"""pongDrillPlacement::GetConfigName (slot 18, 0x8210CC60)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillPlacement::GetConfigName"
ADDRESS = 0x8210CC60
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    t.args(r3=t.alloc(0x60, "drill"))
