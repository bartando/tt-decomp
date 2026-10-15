"""pongPlayer_SetupServe (0x82192F00).

Calls the player's vtable slot 9 (byte offset 0x24, OnButtonReleased), so the
player gets a fake vtable. SelectShotType and SetGravity are stubs; the
shot record lives in the image's table at 0x8261A3D0.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import match_settings, shot_entry  # noqa: E402

FUNCTION = "pongPlayer_SetupServe"
ADDRESS = 0x82192F00
SOURCE = "src/game/player/pong_player.cpp"


def shot_type(ctx):
    return ctx.rng.choice([3, 5, 9])


CALLS = {
    0x82391480: stub(),
    0x8240E6D0: stub(ret="void"),
    0x8219F9C0: stub(ret="void"),                     # FinalizeServeSetup(shotTarget)
    "player.vfn_9": stub(ret="void"),
    0x82199A70: stub(ret=shot_type),                  # SelectShotType(flags, index)
    0x821D6100: stub(ret="void", args=("r3", "f1")),  # SetGravity(shot, settings value)
}


def inputs(t):
    rng = t.rng
    idx = rng.randrange(0, 2)
    match_settings(t)
    shot = shot_entry(t, idx)
    t.w16(shot + 0xC6, rng.getrandbits(16))
    t.w32(0x8271A328, t.alloc(0x10, "netTiming"))
    player = t.alloc(0x1A00, "player", ctype="pongPlayerServeLayout")
    t.w32(player, t.vtable("player", 16))
    t.w32(player + 0x1D0, idx)
    t.w32(player + 0x1EC, t.alloc(0x40, "shotTarget"))
    t.w32(player + 0x17F0, t.alloc(0x30, "sub17F0"))
    t.args(r3=player)
