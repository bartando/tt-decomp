"""Recovered game-state receiver and clock fields for the bank-selection predicate."""
from liftcheck.spec import *
FUNCTION = "BallPredict_ShouldUsePrevious"
ADDRESS = 0x821D3390
SOURCE = "src/game/ball/ball_playback.cpp"
TRIALS = 800


def inputs(t):
    rng = t.rng
    state = t.alloc(0x40, "game state")
    data = t.alloc(0x2800, "prediction")
    t.w32(state + 0x14, data)
    tail = rng.choice([0, 1, 118, 119, rng.randrange(120)])
    t.w32(data + 0x25A4, tail)
    t.w32(data + 0x25A8, rng.choice([-1, 0, 1, 2, 3, 120]))
    vals = [0.0, -0.0, 0.25, 1.0, -1.0, 2.0, float("nan"), float("inf")]
    t.wf32(state + 4, rng.choice(vals))
    t.wf32(state + 0xC, rng.choice(vals))
    for i in range(120):
        t.wf32(data + 0x20 + 0x50 * i, rng.choice(vals))
    t.args(r3=state, f1=rng.uniform(-100, 100), f2=rng.uniform(-100, 100))
