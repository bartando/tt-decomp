"""0x821D8538: first net flag, stopping at the floor; NaN height keeps scanning."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_hit_queries_common import inputs as build
FUNCTION = "BallPredict_FindNetContact"
ADDRESS = 0x821D8538
SOURCE = "src/game/ball/ball_prediction_hit_queries.cpp"
TRIALS = 800


def inputs(t):
    build(t, "net")
