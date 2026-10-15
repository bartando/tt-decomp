"""pongDrillMovement::Finish (slot 5, 0x8210DC48): base finish, then the HUD arrow."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::Finish"
ADDRESS = 0x8210DC48
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    t.w32(0x82606614, t.alloc(0xC0, "hud"))
    drill = t.alloc(0x40, "drill")
    t.w32(drill, t.vtable("drill", slots=33))
    t.args(r3=drill)
