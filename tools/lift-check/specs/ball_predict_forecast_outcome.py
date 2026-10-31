"""0x8228A688: finite-vector validation, outcome priority and 120-step bound."""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_outcome_helpers_common import FORECAST_CALLS as CALLS, forecast_inputs as inputs
FUNCTION = "BallPredict_ForecastOutcome"
ADDRESS = 0x8228A688
SOURCE = "src/game/ball/ball_prediction_outcome_helpers.cpp"
TRIALS = 800
