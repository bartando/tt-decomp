"""0x820DC8E0: signed frame marker / 30 / clip duration, rounded at each step."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _player_swing_phase_common import *

FUNCTION = "game_C8E0_h"
ADDRESS = 0x820DC8E0
SOURCE = "src/game/player/player_swing_phase.cpp"
TRIALS = 1000


def inputs(t):
    t.args(r3=state(t))
