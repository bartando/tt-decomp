"""0x8224CDF0: protected clips, stop/reset sequence, low-byte loop flags."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _anim_blender_state_common import *

FUNCTION = "util_CDF0"
ADDRESS = 0x8224CDF0
SOURCE = "src/anim/anim_blender_state.cpp"
TRIALS = 1000
CALLS = dict(CALLBACKS)
CALLS.update({0x8224CEA8: run(), 0x8224C810: run()})


def inputs(t):
    obj = state(t)
    clip = t.alloc(0x40, "clip")
    t.args(r3=obj, r4=clip, r5=t.rng.choice([0, 1, 0x100, 0x101, -1, 0xFFFF0000]))
