"""gdBallPredictData::AddSample (0x821D7C10): push onto the ring unless it's full."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import predict_data, fill_sample

FUNCTION = "gdBallPredictData::AddSample"
ADDRESS = 0x821D7C10
SOURCE = "src/game/ball/ball_predict.cpp"
EXTERNS = {"gdBallPredictSample::operator=": 0x820D6E58}
CALLS = {0x820D6E58: run()}


def inputs(t):
    d, _, _ = predict_data(t)
    if t.rng.random() < 0.2:
        t.w32(d + 0x25A0, 119)
    s = t.alloc(0x50, "src", ctype="gdBallPredictSample")
    fill_sample(t, s)
    t.args(r3=d, r4=s)
