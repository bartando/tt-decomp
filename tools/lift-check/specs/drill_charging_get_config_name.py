"""pongDrillCharging::GetConfigName (slot 18, 0x8210CCB0)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillCharging::GetConfigName"
ADDRESS = 0x8210CCB0
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    t.args(r3=t.alloc(0x60, "drill"))
