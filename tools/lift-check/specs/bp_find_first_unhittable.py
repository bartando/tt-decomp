"""gdBallPredictData::FindFirstUnhittableFrom (0x821D8A30)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import predict_data

FUNCTION = "gdBallPredictData::FindFirstUnhittableFrom"
ADDRESS = 0x821D8A30
SOURCE = "src/game/ball/ball_predict.cpp"


def inputs(t):
    d, _, count = predict_data(t)
    t.args(r3=d, r4=t.rng.randrange(0, count + 2))
