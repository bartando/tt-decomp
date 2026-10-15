"""pongCSAction::Seek (slot 9, 0x823493F8): calls slot 9 on every child with its r4 (an int, not the float the header had) (through the game's
vtable; the header's C++ virtuals were dropped)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from _cs_action import cs_action  # noqa: E402

FUNCTION = "pongCSAction::Seek"
ADDRESS = 0x823493F8
SOURCE = "src/game/cutscene/pong_cutscene.cpp"

CALLS = {
    "child.vfn_9": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    act = cs_action(t)
    t.args(r3=act, r4=t.u32())
