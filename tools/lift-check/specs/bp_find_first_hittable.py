"""gdBallPredictData::FindFirstHittable (0x821D8990)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import predict_data

FUNCTION = "gdBallPredictData::FindFirstHittable"
ADDRESS = 0x821D8990
SOURCE = "src/game/ball/ball_predict.cpp"


def inputs(t):
    d, _, _ = predict_data(t)
    t.args(r3=d)
