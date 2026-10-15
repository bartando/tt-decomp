"""pongPlayerState::IsBeforeSwingPeak (0x820CDCD8).

The original inlines 0x820CD550 (IsSwingTimerActive) and calls 0x820CD598;
the lift calls both. The recovery blender's window check (0x820DD298) is a
stub returning 0 or 1.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import PREDICATES, coin, player_state  # noqa: E402

FUNCTION = "pongPlayerState::IsBeforeSwingPeak"
ADDRESS = 0x820CDCD8
SOURCE = "src/game/player/pong_player.cpp"

CALLS = dict(PREDICATES)
CALLS[0x820DD298] = stub(ret=coin)   # pongPlayer_IsWithinTimingWindow(recovery)


def inputs(t):
    t.args(r3=player_state(t))
