"""pongPlayer_EnterServeMode (0x82192668).

GetServeBallBody is inlined in both (level slot 4, else 0x822C4980 after an
optional game_3860 log). CheckServeInput is a 0/1 stub; the asm can call it
twice.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import ball_inst, coin, match_settings, physics  # noqa: E402

FUNCTION = "pongPlayer_EnterServeMode"
ADDRESS = 0x82192668
SOURCE = "src/game/player/pong_player.cpp"


def maybe_body(ctx):
    return ctx.rng.choice([0, 0x40001000])


# The symbol map has two game_3860s and by_name picks 0x82483860; the one
# the build links (pong_match.cpp, `// @ 0x821D3860`) is the asm's callee.
EXTERNS = {"game_3860": 0x821D3860}

CALLS = {
    "level.vfn_4": stub(ret=maybe_body, args=("r3", "r4")),
    0x822C4980: stub(),
    0x821D3860: stub(ret="void"),            # game_3860(gameState, 1, name)
    0x82195B60: stub(ret=coin),              # CheckServeInput
    0x8218EAA8: stub(ret="void"),            # PlaceBallInHand(player, ball)
    0x82195C00: stub(ret="void"),            # move mode
}


def inputs(t):
    rng = t.rng
    idx = rng.randrange(0, 2)
    match_settings(t)
    gs = t.alloc(0x20, "gameState", fill="zero")
    sub = t.alloc(0x25B0, "gameState.sub14", fill="zero")
    t.w32(sub + 0x25A8, rng.choice([0, 1, -1]))
    t.w32(gs + 0x14, sub)
    t.w32(0x8271A2F8, gs)
    player = t.alloc(0x200, "player", fill="zero")
    inst, bidx = ball_inst(t)
    physics(t, bidx)
    t.w32(player + 0x1C0, inst)
    t.w32(player + 0x1CC, rng.choice([0, 2, 4, 3]))
    t.w32(player + 0x1D0, idx)
    ai = t.alloc(0x40, "ai", fill="zero")
    s34 = t.alloc(0x10, "ai.sub34", fill="zero")
    t.wf32(s34 + 4, rng.choice([0.0, -1.0, 1.0, rng.uniform(-1, 1)]))
    t.w32(ai + 0x34, s34)
    t.w32(player + 0x1F0, ai)
    t.args(r3=player)
