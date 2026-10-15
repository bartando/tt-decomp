"""pongPlayer_PlaceBallInHand (0x8218EAA8).

0x820CE090 fills the 64-byte hold matrix (an out-param on the stack, filled by
the default stub); the instance gets it, +0xA0 moves to +0xB0 and +0xA0 takes
g_identityVector (0x82606740).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import ball_inst, physics  # noqa: E402

FUNCTION = "pongPlayer_PlaceBallInHand"
ADDRESS = 0x8218EAA8
SOURCE = "src/game/player/pong_player.cpp"

CALLS = {
    0x820CE090: stub(ret="void", out={"r4": 0x40}),
    "inst.vfn_3": stub(ret="void", args=("r3", "r4")),
    "ball.vfn_1": stub(ret="void"),
    "level.vfn_11": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    player = t.alloc(0x200, "player", fill="zero")
    creature = t.alloc(0xD0, "creature", fill="zero")
    t.w32(creature + 0xBC, t.alloc(0x100, "blender"))
    t.w32(player + 0x1C4, creature)
    inst, idx = ball_inst(t)
    physics(t, idx)
    t.w32(player + 0x1C0, inst)
    ball = 0
    if rng.random() < 0.8:
        ball = t.alloc(0x10, "ball", fill="zero")
        t.w32(ball, t.vtable("ball"))
    t.args(r3=player, r4=ball)
