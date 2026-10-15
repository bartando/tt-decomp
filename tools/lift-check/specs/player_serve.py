"""pongPlayer_Serve (0x82193298): the serve callback.

GetServeBallBody returns the ball the inputs parked at player+0x1F8 (a spot
Serve doesn't read). Everything Serve calls is a stub with its arguments
compared; the bounce depth goes to player+0x1C8.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import (BALL_SLOT, match_clock, match_settings, r32, serve_creature,  # noqa: E402
                           shot_entry, table_dims)

FUNCTION = "pongPlayer_Serve"
ADDRESS = 0x82193298
SOURCE = "src/game/player/pong_player.cpp"
# clang contracts startTime + frames * (1/30) into one fmadds; the asm rounds
# the product first. Near a large match clock that is a few ulps.
FTOL = 1e-5


def parked_ball(ctx):
    ctx.ret(r3=r32(ctx, ctx.r(3) + BALL_SLOT))


CALLS = {
    0x82391480: stub(),                                  # util_1480: timestamp text
    0x8240E6D0: stub(ret="void"),                        # log (format compared by content)
    0x821925C8: model(parked_ball),
    0x8218EAA8: stub(ret="void"),                        # PlaceBallInHand
    0x82195C00: stub(ret="void"),                        # move mode
    "arch.vfn_15": stub(ret="void", args=("r3", "f1")),
    0x821934A0: stub(ret="void"),                        # TossServeBall
    0x8225E6E0: stub(ret="void"),
    0x8219FBD8: stub(ret="void"),                        # AdjustAimDepthForBall
}


def inputs(t):
    rng = t.rng
    idx = rng.randrange(0, 2)
    now = rng.uniform(1, 500)
    match_clock(t, now)
    match_settings(t)
    table_dims(t)
    shot_entry(t, idx)
    t.w32(0x8271A328, t.alloc(0x10, "netTiming"))
    player = t.alloc(0x1A00, "player", fill="zero", ctype="pongPlayerServeLayout")
    t.w32(player + 0x1D0, idx)
    creature, _, _ = serve_creature(t, now)
    t.w32(player + 0x1C4, creature)
    t.w32(player + 0x1EC, t.alloc(0x40, "shotTarget"))
    ball = t.alloc(0xE0, "ball", ctype="pongBallBody")
    inst = t.alloc(0x10, "ballInst", fill="zero")
    arch = t.alloc(0x10, "arch", fill="zero")
    t.w32(arch, t.vtable("arch", 16))
    t.w32(inst + 4, arch)
    t.w32(ball + 0x10, inst)
    t.wf32(ball + 0xD8, rng.uniform(-3.5, 3.5))
    t.w32(player + BALL_SLOT, ball)
    t.args(r3=player)
