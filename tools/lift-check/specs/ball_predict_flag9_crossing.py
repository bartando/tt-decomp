"""Flag9 crossing over the frame interval, wrapped ring, early future stop and NaNs."""
from liftcheck.spec import *

FUNCTION = "BallPredict_HasFlag9Crossing"
ADDRESS = 0x821D7D90
SOURCE = "src/game/ball/ball_prediction_stream.cpp"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    data = t.alloc(0x2800, "predict", ctype="gdBallPredictData")
    tail = rng.randrange(120)
    count = rng.choice([0, 1, 2, 3, 8, 119, 120])
    t.w32(data + 0x25A4, tail)
    t.w32(data + 0x25A8, count)
    values = [-2., -1., -0., 0., 1., 2., float("nan"), float("inf")]
    timing = t.alloc(0x38, "timing")
    t.wf32(timing + 0x30, rng.choice(values))
    t.wf32(timing + 0x34, rng.choice(values))
    t.w32(0x8271A2E8, timing)
    for n in range(120):
        s = data + 0x20 + n * 0x50
        t.wf32(s, rng.choice(values))
        t.w8(s + 9, rng.choice([0, 0, 1, 2, 0x80, 0xff]))
    t.args(r3=data)
