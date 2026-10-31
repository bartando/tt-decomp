"""82284078: both integration legs, plane rewind/bounce, material dispatch,
net/edge reports, limit exits and helper-mutated table/material parameters.
Only initial unused previous-position stack padding is zero-seeded.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from _ball_shot_simulation_common import CALLS, inputs

FUNCTION = "BallShot_SimulateTrajectory"
ADDRESS = 0x82284078
SOURCE = "src/game/ball/ball_shot_simulation.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
