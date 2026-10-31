"""0x8224C810: exact reset fields, callback templates and untouched gaps."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _anim_blender_state_common import *

FUNCTION = "crAnimBlenderState_Init"
ADDRESS = 0x8224C810
SOURCE = "src/anim/anim_blender_state.cpp"
TRIALS = 1000


def inputs(t):
    t.args(r3=state(t))
