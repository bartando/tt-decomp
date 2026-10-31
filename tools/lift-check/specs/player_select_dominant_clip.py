"""0x820DBAA0: sparse three-slot selection, first-wins ties and ordered weights."""
from liftcheck.spec import *

FUNCTION = "game_BAA0"
ADDRESS = 0x820DBAA0
SOURCE = "src/game/player/player_swing_pose_helpers.cpp"
TRIALS = 1000


def inputs(t):
    record = t.alloc(0x30, "layers")
    mask = t.index % 8
    common = t.rng.choice([-1, -0.0, 0, 1, float("nan"), float("inf")])
    for index in range(3):
        clip = t.alloc(0x30, f"clip{index}")
        t.w32(record + 0x10 + index * 4, clip if mask & (1 << index) else 0)
        weight = common if t.index % 3 == 0 else t.rng.choice([
            -2, -1, -0.0, 0, 1, 2, float("nan"), float("inf"), -float("inf"),
            t.rng.uniform(-3, 3)])
        t.wf32(record + 0x1C + index * 4, weight)
    t.args(r3=record)
