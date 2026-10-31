"""0x821D87E8: outside the table and moving farther away, or descending below it."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_hit_queries_common import inputs as build
FUNCTION = "BallPredict_FindDepartingSample"
ADDRESS = 0x821D87E8
SOURCE = "src/game/ball/ball_prediction_hit_queries.cpp"
TRIALS = 800


def inputs(t):
    build(t, "departing")
