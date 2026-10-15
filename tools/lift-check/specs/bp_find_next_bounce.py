"""gdBallPredictData::FindNextBounce (0x821D93F0)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import predict_data, sparse_bounces

FUNCTION = "gdBallPredictData::FindNextBounce"
ADDRESS = 0x821D93F0
SOURCE = "src/game/ball/ball_predict.cpp"


def inputs(t):
    d, tail, count = predict_data(t)
    if t.rng.random() < 0.7:
        sparse_bounces(t, d, tail, count, max_bounces=t.rng.choice([2, 8, 30]))
    t.args(r3=d, r4=t.rng.randrange(-1, count + 2))
