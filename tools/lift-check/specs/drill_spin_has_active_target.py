"""pongDrillSpin::HasActiveTarget (slot 21, 0x8210CD10): the subclass's target index against its threshold."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrillSpin::HasActiveTarget"
ADDRESS = 0x8210CD10
SOURCE = "src/game/drill/pong_drill.cpp"


def inputs(t):
    drill = t.alloc(0x60, "drill")
    t.w32(drill + 0x28, t.rng.choice([0xFFFFFFFF, 0, 1, 2, 0x80000000, t.rng.getrandbits(32)]))
    t.args(r3=drill)
