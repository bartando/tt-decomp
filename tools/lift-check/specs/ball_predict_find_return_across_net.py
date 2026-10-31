"""0x821D85D8: opposite-side sample after a net contact; zero-z early out."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_hit_queries_common import inputs as build
FUNCTION = "BallPredict_FindReturnAcrossNet"
ADDRESS = 0x821D85D8
SOURCE = "src/game/ball/ball_prediction_hit_queries.cpp"
TRIALS = 800


def inputs(t):
    build(t, "return")
