"""pongPlayerState::IsInReturnPosition (0x820CDE98).

The original inlines 0x820CD550 (IsSwingTimerActive) and calls 0x820CD5F0,
0x820CD598 and 0x820D6AA0 (clip done?, a 0/1 stub here). The swing clip is
embedded at pongTimingSubState+0x20: flags at +0x158, frame count at +0x154,
and +0x30 points at a record whose +0xC is the playback speed (sometimes 0,
negative or NaN).
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import PREDICATES, coin, player_state  # noqa: E402

FUNCTION = "pongPlayerState::IsInReturnPosition"
ADDRESS = 0x820CDE98
SOURCE = "src/game/player/pong_player.cpp"

CALLS = dict(PREDICATES)
CALLS[0x820D6AA0] = stub(ret=coin)


def inputs(t):
    rng = t.rng
    st = player_state(t)
    sub = t.alloc(0x160, "swingSub", fill="zero")
    rec = t.alloc(0x10, "velRecord", fill="zero")
    t.w32(sub + 0x30, rec)
    t.wf32(rec + 0xC, rng.choice([0.0, -1.0, math.nan, rng.uniform(0.25, 2.0), rng.uniform(0.25, 2.0)]))
    t.w16(sub + 0x154, rng.choice([0, rng.randrange(1, 90), -rng.randrange(1, 90)]))
    t.w8(sub + 0x158, rng.getrandbits(8) & rng.choice([0, 0xF3, 0xFF]))
    t.w32(st + 0x78, sub)
    t.args(r3=st)
