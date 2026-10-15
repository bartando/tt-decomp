"""pongPlayer_ReadSwingDirectionInput (0x82191B10).

r3 the player, r4 `update`. Pad-driven players: 0x821E04B0 (button test) and
its callee 0x821E0270 run as the original on pad records under *0x8271A31C
(the asm keeps the pad in r5 across those calls); 0x821921D0 (stick octant)
is a 0..9 stub. AI players: 0x821A66A8 leaves r3 (the direction block) as
it was, which the asm relies on. 0x82193A68 and 0x8219EE88 are stubs with
their float arguments compared.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import coin, match_settings, shot_entry  # noqa: E402

FUNCTION = "pongPlayer_ReadSwingDirectionInput"
ADDRESS = 0x82191B10
SOURCE = "src/game/player/pong_player.cpp"


def keep_r3(ctx):
    ctx.ret(r3=ctx.r(3))


def octant(ctx):
    return ctx.rng.randrange(0, 10)


# The asm loads the pad table from 0x8271A31C (lis -0x7d8e; lwz -0x5ce4);
# pong_player.cpp declares it without an address.
EXTERNS = {"g_pPlayerDataTable": 0x8271A31C}

CALLS = {
    0x82195B60: stub(ret=coin),                                   # CheckServeInput
    0x821E04B0: run(),
    0x821E0270: run(),
    0x821921D0: stub(ret=octant),
    0x821A66A8: model(keep_r3),
    0x82193A68: stub(ret="void", args=("r3", "f1", "f2", "f3", "f4")),
    0x8219EE88: stub(ret="void", args=("r3", "r4", "f1", "f2", "f3", "f4")),
}


def pads(t):
    rng = t.rng
    table = t.alloc(0x0C + 4 * 0x328, "padTable", fill="zero")
    t.w32(table + 4, rng.randrange(0, 4))
    t.w32(table + 8, rng.randrange(0, 4))
    for p in range(4):
        rec = table + 0x0C + p * 0x328
        for k in range(4, 8):
            t.w8(rec + k, rng.choice([0, 1]))
        t.w32(rec + 0x31C, t.alloc(0x100, f"pad{p}.buttons"))
    t.w32(0x8271A31C, table)


def inputs(t):
    rng = t.rng
    idx = rng.randrange(0, 2)
    match_settings(t)
    shot = shot_entry(t, idx)
    t.wf32(shot + 0x40, rng.choice([0.0, -0.0, 0.5, -0.5]))      # vec40.x
    pads(t)
    t.w8(0x8260642F, rng.choice([0, 1]))
    if rng.random() < 0.3:
        t.wf32(0x825CAF0C, rng.uniform(0.01, 0.05))
    player = t.alloc(0x1A00, "player", ctype="pongPlayerServeLayout")
    t.w32(player + 0x1D0, idx)
    t.w8(player + 0x1988, rng.random() < 0.2)
    t.w32(player + 0x19DC, rng.getrandbits(32) & rng.choice([0, 0x19, 0x11, 0x09, 0x1F]))
    t.floats(player + 0x18D0, 4, -1, 1)
    t.w32(player + 0x1EC, t.alloc(0x40, "shotTarget"))
    ai = t.alloc(0x500, "ai", fill="zero")
    d = t.alloc(0x60, "ai.swingDir", fill="zero")
    for k in range(4):
        t.wf32(d + 4 + 4 * k, rng.choice([0.0, 1.0, rng.uniform(0, 1)]))
    t.w8(d + 0x58, rng.choice([0, 1]))
    t.w32(ai + 0x38, d)
    t.wf32(ai + 0x4BC, rng.uniform(0, 1))
    t.wf32(ai + 0x4C0, rng.uniform(0, 1))
    t.w8(ai + 0x4E1, rng.choice([0, 1]))
    t.w32(player + 0x1F0, ai)
    t.args(r3=player, r4=rng.choice([0, 1]))
