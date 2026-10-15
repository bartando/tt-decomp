"""pongPlayerState::IsSwingSystemIdle (0x820CDDC0): five blender predicates.

The original calls 0x820CD5F0/D660/D6B8/D598 and inlines 0x820CD550
(IsSwingTimerActive); the lift calls all five. Every predicate runs as the
original code; the inlined one is left out of the call trace.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import PREDICATES, player_state  # noqa: E402

FUNCTION = "pongPlayerState::IsSwingSystemIdle"
ADDRESS = 0x820CDDC0
SOURCE = "src/game/player/pong_player.cpp"

CALLS = dict(PREDICATES)


def inputs(t):
    t.args(r3=player_state(t))
