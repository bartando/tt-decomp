"""0x82289B10: serve/non-serve outcomes, fallback queries and hittable windows."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_hit_ids_common import CALLS, inputs

FUNCTION = "BallPredict_BuildHitIds"
ADDRESS = 0x82289B10
SOURCE = "src/game/ball/ball_prediction_hit_ids.cpp"
TRIALS = 800
