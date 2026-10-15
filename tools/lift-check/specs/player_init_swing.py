"""pongPlayer_InitSwing (0x82190780).

Resets the shot record (image table at 0x8261A3D0) and swing input; calls the
player's vtable slot 9, SelectShotType, SetGravity and
ReadSwingDirectionInput (stubs, arguments compared). Scores come from
*0x825EAB2C. The dot3 runs on the vector unit (vmsum3fp128), hence FTOL.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import match_settings, shot_entry  # noqa: E402

FUNCTION = "pongPlayer_InitSwing"
ADDRESS = 0x82190780
SOURCE = "src/game/player/pong_player.cpp"
FTOL = 1e-5


def log_and_clear_w(ctx):
    """The original builds vecF0's zero on the stack at 0x50(r1), writing x, y
    and z only, then copies all 16 bytes: its w lane is whatever the stack
    held (lift-check fills it with random bytes). The lift writes 0. On the
    original's side, clear that slot during the first log call, which runs on
    InitSwing's frame before the vector is built."""
    if ctx.side == "orig":
        ctx.write(ctx.m.gpr(1) + 0x50, bytes(16))


def shot_type(ctx):
    return ctx.rng.choice([3, 5, 9])


CALLS = {
    0x8240E6D0: model(log_and_clear_w),
    0x8219F9C0: stub(ret="void"),                     # FinalizeServeSetup(shotTarget)
    "player.vfn_9": stub(ret="void"),
    0x82199A70: stub(ret=shot_type),
    0x821D6100: stub(ret="void", args=("r3", "f1")),
    0x82191B10: stub(ret="void"),                     # ReadSwingDirectionInput(player, false)
}


def inputs(t):
    rng = t.rng
    idx = rng.randrange(0, 2)
    match_settings(t)
    shot = shot_entry(t, idx)
    t.w16(shot + 0xC6, rng.getrandbits(16))
    t.w8(shot + 0xD4, 0xAA)
    t.w8(shot + 0xD5, rng.choice([0, 1]))
    t.w8(shot + 0x150, 0xAA)
    # bring targetPos and vec60 close enough that the excess over 7 goes both ways
    t.floats(shot + 0x60, 3, -2, 2)
    score = t.alloc(0x24, "score")
    t.w32(0x825EAB2C, score)
    t.wf32(0x825C7598, rng.choice([7.0, rng.uniform(0, 10)]))   # lbl_825C7598 (.data)
    player = t.alloc(0x1A00, "player", ctype="pongPlayerServeLayout")
    t.w32(player, t.vtable("player", 16))
    t.w32(player + 0x1D0, idx)
    t.w32(player + 0x1EC, t.alloc(0xEB0, "shotTarget"))
    t.w32(player + 0x17F0, t.alloc(0x30, "sub17F0"))
    t.args(r3=player)
