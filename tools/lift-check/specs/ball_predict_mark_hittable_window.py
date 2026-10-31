"""0x821D38E8: skip contact run, then mark until a low sample or next contact."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_outcome_helpers_common import window_inputs as inputs
FUNCTION = "BallPredict_MarkHittableWindow"
ADDRESS = 0x821D38E8
SOURCE = "src/game/ball/ball_prediction_outcome_helpers.cpp"
TRIALS = 800
