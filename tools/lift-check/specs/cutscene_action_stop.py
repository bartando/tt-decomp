"""pongCSAction::Stop (slot 6, 0x82349318): calls slot 6 on every child (through the game's
vtable; the header's C++ virtuals were dropped)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from _cs_action import cs_action  # noqa: E402

FUNCTION = "pongCSAction::Stop"
ADDRESS = 0x82349318
SOURCE = "src/game/cutscene/pong_cutscene.cpp"

CALLS = {
    "child.vfn_6": stub(ret="void"),
}


def inputs(t):
    act = cs_action(t)
    t.args(r3=act)
