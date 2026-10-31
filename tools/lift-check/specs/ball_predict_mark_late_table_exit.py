"""0x8228A4E8: sufficiently late low hittable sample inside strict rectangle."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_outcome_helpers_common import late_inputs as inputs
FUNCTION = "BallPredict_MarkLateTableExit"
ADDRESS = 0x8228A4E8
SOURCE = "src/game/ball/ball_prediction_outcome_helpers.cpp"
TRIALS = 800
