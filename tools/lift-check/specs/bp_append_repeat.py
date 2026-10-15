"""gdBallPredictData::AppendRepeatOfLast (0x821D7C88): last sample again, 1 s later."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import predict_data, EXTERNS  # noqa: F401

FUNCTION = "gdBallPredictData::AppendRepeatOfLast"
ADDRESS = 0x821D7C88
SOURCE = "src/game/ball/ball_predict.cpp"
CALLS = {0x821D7C10: run(), 0x820D6E58: run()}


def inputs(t):
    d, _, _ = predict_data(t)
    t.args(r3=d)
