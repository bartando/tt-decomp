"""pongPlayer_StartServe (0x82193190).

The two callbacks handed to pongCreature_StartServeBlender live on the stack;
their 16 bytes (target, function, data, kind) are compared as const pointees.
io_Input_poll_9D68 runs as the original on the settings object.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import match_settings, shot_entry  # noqa: E402

FUNCTION = "pongPlayer_StartServe"
ADDRESS = 0x82193190
SOURCE = "src/game/player/pong_player.cpp"

CALLS = {
    0x82391480: stub(),
    0x8240E6D0: stub(ret="void"),
    "io_Input_poll_9D68": run(),
    0x820C7248: stub(ret="void", deref={"r4": 16, "r5": 16}),
    0x8225E6E0: stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    idx = rng.randrange(0, 2)
    match_settings(t)
    shot_entry(t, idx)
    t.w32(0x8271A328, t.alloc(0x10, "netTiming"))
    player = t.alloc(0x1A00, "player", ctype="pongPlayerServeLayout")
    t.w32(player + 0x1D0, idx)
    t.w32(player + 0x1C4, t.alloc(0xD0, "creature"))
    t.args(r3=player)
