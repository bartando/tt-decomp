"""pongPlayer_D550_g (0x820CD550): pongPlayerState predicate."""
from liftcheck.spec import *  # noqa: F401,F403
import math

FUNCTION = "pongPlayer_D550_g"
ADDRESS = 0x820CD550
SOURCE = "src/game/player/player_state_queries.cpp"


def f(rng):
    return rng.choice([0.0, -0.0, 1.0, 0.5, 2.0, -1.0, rng.uniform(-3, 3), math.nan, math.inf])


def inputs(t):
    rng = t.rng
    state = t.alloc(0x90, "state", fill="zero")
    sub = t.alloc(0x1A0, "sub")
    for off in (0x1C, 0x30, 0xAC, 0x19C):
        t.wf32(sub + off, f(rng))
    t.w8(sub + 0x2C, rng.choice([0, 0, 1, 0x80]))
    t.w16(sub + 0x5A, rng.choice([0, 1, 2, 0xFFFF]))
    if rng.random() < 0.9:
        for off in (0x7C, 0x80, 0x88):
            t.w32(state + off, sub)
    t.args(r3=state)
