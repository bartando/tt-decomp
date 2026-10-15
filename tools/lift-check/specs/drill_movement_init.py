"""pongDrillMovement::Init (slot 3, 0x8210DB48): the base reset inline, then a full clock."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::Init"
ADDRESS = 0x8210DB48
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    data = t.alloc(0x80, "movementData")
    t.floats(data + 0x60, 7, 0.0, 60.0)
    drill = t.alloc(0x40, "drill")
    t.w32(drill + 0x38, data)
    t.args(r3=drill)
