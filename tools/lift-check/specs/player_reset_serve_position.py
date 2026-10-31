"""0x821936D8: opposite handedness byte and actual alternate-pose flag."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _player_mover_callers_common import *

FUNCTION = "pongPlayer::ResetServePosition"
ADDRESS = 0x821936D8
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000
CALLS = {
    0x82193628: stub(ret="void", args=("r3", "r4")),
    0x8218C690: stub(ret=lambda c: c.rng.randrange(2)),
    0x820C9F40: stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    t.args(r3=player(t))
