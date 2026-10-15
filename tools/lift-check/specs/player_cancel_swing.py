"""pongPlayerState::CancelSwing (0x820CD908): resets whichever blender runs.

The original inlines 0x820CD550 (IsSwingTimerActive) and calls
0x820CD598/0x820CD5F0; the lift calls all three. The timer reset writes a
byte to 0x8260633C and a word to 0x82606340 in the image.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import PREDICATES, player_state  # noqa: E402

FUNCTION = "pongPlayerState::CancelSwing"
ADDRESS = 0x820CD908
SOURCE = "src/game/player/pong_player.cpp"

# pong_player.hpp marks them "@ lis(-32160)+25404/+25408".
EXTERNS = {"g_swingInFlightFlag": 0x8260633C, "g_swingCountFlag": 0x82606340}

CALLS = dict(PREDICATES)
CALLS.update({
    0x8240E6D0: stub(ret="void"),   # log (format string compared by content)
    0x820DCD20: stub(ret="void"),   # game_CD20: clears the serve blender
    0x8224C810: stub(ret="void"),   # crAnimBlenderState_Init(anim+0x10)
})


def inputs(t):
    st = player_state(t)
    t.w32(st + 0x08, t.u32())                          # printed as the player number
    t.w32(0x8260633C, 0xA5A5A5A5)
    t.w32(0x82606340, 0x5A5A5A5A)
    t.args(r3=st)
