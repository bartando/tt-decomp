"""0x820DC7A0: activate a swing clip, set phase and send its slot event."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _player_swing_phase_common import *

FUNCTION = "pg_C7A0_g"
ADDRESS = 0x820DC7A0
SOURCE = "src/game/player/player_swing_phase.cpp"
TRIALS = 1000


def started(ctx):
    return ctx.rng.choice([0, 1, 0x100, 0x101, 0xFFFFFFFF, 0xFFFF0000])


CALLS = {
    0x8224CDF0: stub(ret=started, args=("r3", "r4", "r5")),
    0x8225E6E0: stub(ret="void", args=("r3", "r4", "r5", "r6")),
}


def inputs(t):
    obj = state(t)
    t.args(r3=obj, f1=t.rng.choice([
        -1.0, -0.0, 0.0, 0.01, 1.0, 10.0, float("nan"),
        float("inf"), -float("inf"), t.rng.uniform(0.0, 5.0)]))
