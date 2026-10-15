"""gdBallPredictData::CountBouncesSoFar (0x821D91C0)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import DATA_SIZE, EXTERNS  # noqa: F401

FUNCTION = "gdBallPredictData::CountBouncesSoFar"
ADDRESS = 0x821D91C0
SOURCE = "src/game/ball/ball_predict.cpp"


def inputs(t):
    rng = t.rng
    d = t.alloc(DATA_SIZE, "predict", ctype="gdBallPredictData")
    n = rng.randrange(-1, 11)
    t.w32(d + 0x27E0, n)
    for k in range(10):
        t.wf32(d + 0x2790 + 8 * k, rng.uniform(0.0, 5.0))
        t.w8(d + 0x2794 + 8 * k, rng.choice([0, 1, 2]))
    timing = t.alloc(0x40, "timing")
    t.wf32(timing + 0x30, rng.uniform(0.0, 5.0))
    t.w32(0x8271A2E8, timing)
    t.args(r3=d, r4=t.alloc(4, "local"), r5=t.alloc(4, "other"))
