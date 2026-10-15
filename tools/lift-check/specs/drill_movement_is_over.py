"""pongDrillMovement::IsOver (slot 22, 0x8210CBF0, re-homed): the finished byte as is."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillMovement::IsOver"
ADDRESS = 0x8210CBF0
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    drill = t.alloc(0x40, "drill")
    t.w8(drill + 0x24, t.rng.choice([0, 1]))  # a bool: the game only ever stores 0 or 1
    t.args(r3=drill)
