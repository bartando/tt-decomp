"""0x821D6360: rectangle deltas, both clamp bounds and conversion output."""
from liftcheck.spec import *

FUNCTION = "pongPlayer_6360_g"
ADDRESS = 0x821D6360
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 500
CALLS = {0x821D4EA0: run(), 0x821D5010: stub(ret="void", args=("r3", "r4", "r5", "r6"), deref={"r3": 16})}


def inputs(t):
    state = t.alloc(0x60, "state", floats=[(0x40, 8)])
    rect = t.alloc(16, "rect", floats=[(0, 4)])
    t.floats(state + 0x40, 8, -3, 3)
    t.floats(rect, 4, -3, 3)
    t.args(r3=state, r4=rect, f1=t.rng.uniform(-10, 10), f2=t.rng.uniform(-10, 10))
