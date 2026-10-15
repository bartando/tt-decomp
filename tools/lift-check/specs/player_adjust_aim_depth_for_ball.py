"""shotTarget_AdjustAimDepthForBall (0x8219FBD8): a shotTarget method.

r3 the shotTarget (+0x2C its pongPlayer, whose +0x1D0 is the player index),
r4 the ball body (position.z at +0xD8). Writes the shot record's aimNorm in
the image's table at 0x8261A3D0.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import match_settings, shot_entry, table_dims  # noqa: E402

FUNCTION = "shotTarget_AdjustAimDepthForBall"
ADDRESS = 0x8219FBD8
SOURCE = "src/game/player/pong_player.cpp"
FTOL = 1e-6


def inputs(t):
    rng = t.rng
    idx = rng.randrange(0, 2)
    player = t.alloc(0x200, "player", fill="zero")
    t.w32(player + 0x1D0, idx)
    target = t.alloc(0x30, "shotTarget", fill="zero")
    t.w32(target + 0x2C, player)
    table_dims(t)
    match_settings(t)
    shot = shot_entry(t, idx)
    t.wf32(shot + 0x28, rng.uniform(-1.5, 1.5))               # targetPos.z near the net
    ball = t.alloc(0xE0, "ball", ctype="pongBallBody")
    t.wf32(ball + 0xD8, rng.uniform(-4, 4))
    t.args(r3=target, r4=ball)
