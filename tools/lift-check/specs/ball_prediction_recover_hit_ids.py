"""0x82289E90..0x8228A4E0: recovery across all forecast outcomes and sides."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_hit_ids_common import CALLS, inputs as common_inputs

FUNCTION = "BallPredict_RecoverHitIds"
ADDRESS = 0x82289E90
SOURCE = "src/game/ball/ball_prediction_hit_ids.cpp"
TRIALS = 800


def inputs(t):
    common_inputs(t, recovery=True)
