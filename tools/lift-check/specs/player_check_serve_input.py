"""pongPlayer_CheckServeInput (0x82195B60)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import match_settings  # noqa: E402

FUNCTION = "pongPlayer_CheckServeInput"
ADDRESS = 0x82195B60
SOURCE = "src/game/player/pong_player.cpp"

# The original keeps r7/r9 across this leaf call, so it runs as is.
CALLS = {"io_Input_poll_9D68": run()}


def inputs(t):
    match_settings(t)
    player = t.alloc(0x200, "player", fill="zero")
    t.w32(player + 0x1D0, t.rng.randrange(0, 2))
    t.args(r3=player)
