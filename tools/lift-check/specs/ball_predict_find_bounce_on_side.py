"""0x821D8440: post-air contact, side mismatch and -1/-2/-3 outcomes."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_hit_queries_common import inputs as build
FUNCTION = "BallPredict_FindBounceOnSide"
ADDRESS = 0x821D8440
SOURCE = "src/game/ball/ball_prediction_hit_queries.cpp"
TRIALS = 800


def inputs(t):
    build(t, "bounce")
