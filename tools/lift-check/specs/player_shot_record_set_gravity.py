"""pongShotRecord_SetGravity (0x821D6100): fsel clamp and a fall-through switch."""
import math

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongShotRecord_SetGravity"
ADDRESS = 0x821D6100
SOURCE = "src/game/player/pong_player.cpp"


def inputs(t):
    rng = t.rng
    shot = t.alloc(0xA0, "shot", ctype="pongShotRecord")
    t.w32(shot + 0x9C, rng.choice([3, 5, 7, 8, 9, 10, 11]))
    if rng.random() < 0.3:
        t.wf32(0x825CBCE4, rng.uniform(-15, -5))          # g_ballGravity (.data)
    x = rng.choice([rng.uniform(-2, 2), -0.9, 0.0, math.nan, rng.uniform(-1, -0.8)])
    t.args(r3=shot, f1=x)
