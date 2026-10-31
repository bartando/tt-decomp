"""0x8224CEA8: callback ordering and cleanup of an active clip."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _anim_blender_state_common import *

FUNCTION = "crAnimBlenderState_Stop"
ADDRESS = 0x8224CEA8
SOURCE = "src/anim/anim_blender_state.cpp"
TRIALS = 1000
CALLS = CALLBACKS


def inputs(t):
    t.args(r3=state(t))
