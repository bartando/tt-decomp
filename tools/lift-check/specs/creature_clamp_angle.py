"""0x823DA1F8: wrapped angular limits, full-turn bypass, crossing/ties/NaNs.

Execute the real wrap and closer routines. Remainder is the sole modeled
boundary. Compare every call, float and return exactly; no ignored ranges.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _creature_angle_common import *

FUNCTION = 'LocomotionStateAnim_A1F8_g'
ADDRESS = 0x823DA1F8
SOURCE = 'src/anim/angle_helpers.cpp'
TRIALS = 1200
FP_CONTRACT = 'off'
CALLS = {**CALLS, 0x820DF0A8: run(args=('f1',)), 0x823DA190: run(args=('f1', 'f2', 'f3'))}


def inputs(t):
    rng = t.rng
    value, low, high = (rng.uniform(-20, 20) for _ in range(3))
    mode = t.index % 12
    if mode < 3:
        low, high = -2., 2.
        value = (-2., 0., 2.)[mode]
    elif mode == 3: low, high, value = 2.5, -2.5, rng.choice((-3., 3., 0.))
    elif mode == 4: low, high = 1., 1.
    elif mode in (5, 6, 7): low, high = 0., (6.283184051513672, 6.28318452835083, 6.283185005187988)[mode - 5]
    elif mode == 8: low, high = -10., 10.
    elif mode == 9: value = float('nan')
    elif mode == 10: low = float('nan')
    elif mode == 11: high = rng.choice((float('nan'), float('inf'), -float('inf')))
    t.args(f1=value, f2=low, f3=high, r3=rng.getrandbits(32))
