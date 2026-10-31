"""0x820DF0A8: float-rounded shift, double remainder, -pi canonicalization.

Test zeros, +/-pi and adjacent floats, large finite angles, infinities and NaNs.
No memory exclusions or numerical tolerance. CRT remainder alone is modeled.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _creature_angle_common import *

FUNCTION = 'LocomotionStateAnim_WrapAngle'
ADDRESS = 0x820DF0A8
SOURCE = 'src/anim/angle_helpers.cpp'
TRIALS = 1000
FP_CONTRACT = 'off'


def inputs(t):
    choices = (0., -0., 3.1415927410125732, -3.1415927410125732,
               3.141592502593994, 3.1415929794311523, -3.141592502593994,
               6.2831854820251465, -6.2831854820251465, 1e-40, -1e-40,
               1e30, -1e30, float('inf'), -float('inf'), float('nan'))
    value = choices[t.index % len(choices)] if t.index % 3 else t.rng.uniform(-1e6, 1e6)
    t.args(f1=value, r3=t.rng.getrandbits(32))
