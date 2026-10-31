"""0x821D8AD0: last-sample sign bits, table margins and side threshold at -1."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_hit_queries_common import inputs as build
FUNCTION = "BallPredict_NeedsOutcomeForecast"
ADDRESS = 0x821D8AD0
SOURCE = "src/game/ball/ball_prediction_hit_queries.cpp"
TRIALS = 800


def inputs(t):
    build(t, "forecast")
