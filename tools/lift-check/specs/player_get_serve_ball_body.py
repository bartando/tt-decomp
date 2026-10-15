"""pongPlayer_GetServeBallBody (0x821925C8)."""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import ball_inst, physics  # noqa: E402


def maybe_body(ctx):
    return ctx.rng.choice([0, 0x40001000])


FUNCTION = "pongPlayer_GetServeBallBody"
ADDRESS = 0x821925C8
SOURCE = "src/game/player/pong_player.cpp"

CALLS = {
    "level.vfn_4": stub(ret=maybe_body, args=("r3", "r4")),   # GetActiveBody(level, index)
    0x822C4980: stub(),                                       # activate: random body
}


def inputs(t):
    player = t.alloc(0x200, "player", fill="zero")
    inst, idx = ball_inst(t)
    physics(t, idx)
    t.w32(player + 0x1C0, inst)
    t.args(r3=player)
