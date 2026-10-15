"""pongCSAction::Pause (slot 7, 0x823492B0): calls slot 7 on every child (through the game's
vtable; the header's C++ virtuals were dropped)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from _cs_action import cs_action  # noqa: E402

FUNCTION = "pongCSAction::Pause"
ADDRESS = 0x823492B0
SOURCE = "src/game/cutscene/pong_cutscene.cpp"

CALLS = {
    "child.vfn_7": stub(ret="void", args=("r3", "f1")),
}


def inputs(t):
    act = cs_action(t)
    t.args(r3=act, f1=t.rng.uniform(-2.0, 2.0))
