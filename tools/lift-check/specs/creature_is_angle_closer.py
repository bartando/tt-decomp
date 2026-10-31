"""0x823DA190: compare wrapped angular distances; ties and NaNs return false."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _creature_angle_common import *

FUNCTION = 'LocomotionStateAnim::IsAngleCloser'
ADDRESS = 0x823DA190
SOURCE = 'src/anim/angle_helpers.cpp'
TRIALS = 1000
FP_CONTRACT = 'off'
CALLS = {**CALLS, 0x820DF0A8: run(args=('f1',))}


def inputs(t):
    rng = t.rng
    target = rng.uniform(-20, 20)
    angles = (rng.uniform(-20, 20), rng.uniform(-20, 20))
    if t.index % 5 == 0: angles = (target - 1, target + 1)
    if t.index % 5 == 1: target, angles = 3.1, (-3.1, 2.)
    if t.index % 5 == 2: angles = (float('nan'), rng.uniform(-10, 10))
    if t.index % 5 == 3: angles = (target, target)
    t.args(f1=target, f2=angles[0], f3=angles[1], r3=rng.getrandbits(32))
