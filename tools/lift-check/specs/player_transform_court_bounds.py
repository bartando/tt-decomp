"""0x820D8B90: live court query, nonzero side index, affine transform and min/max swap.
Run default 1000 trials with --seed 1 and --seed 7.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _swing_common import *

FUNCTION = "pongPlayer_8B90_fw"
ADDRESS = 0x820D8B90
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
CALLS = {0x821C9CD0: run()}


def inputs(t):
    settings(t)
    obj = t.alloc(0x200, "player")
    t.w32(obj + 0x190, t.pick(range(8)))
    matrix = t.alloc(64, "transform")
    t.floats(matrix, 16, -10, 10)
    lo = t.alloc(16, "lower", floats=[(0, 4)])
    hi = t.alloc(16, "upper", floats=[(0, 4)])
    if t.index % 8 == 0:
        hi = lo
    t.args(r3=obj, r4=matrix, r5=lo, r6=hi)
