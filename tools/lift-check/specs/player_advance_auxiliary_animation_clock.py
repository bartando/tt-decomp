"""820C28B0: live/replay rate, duration normalization, fused phase, reset at 1.

The real replay-rate helper runs on both sides. Durations include nonpositive
values and NaN; phase includes negative values and exact wrap boundaries.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from liftcheck.spec import run
from _animation_clock_common import *

FUNCTION = "LocomotionStateAnim_28B0_w"
ADDRESS = 0x820C28B0
CALLS = {0x821CCBD0: run(args=("r3",))}


def inputs(t):
    replay = replay_inputs(t)
    t.w32(replay + 0x68CF0, [0, 1, 1, 2, -1][t.index % 5])
    t.w32(t.sym("g_pReplayStateData"), replay)
    t.wf32(t.sym("g_sysTimeManager") + 8, edge(t))
    entry = t.alloc(0x20, "entry")
    clip = t.alloc(0x10, "clip")
    t.w32(entry + 0x1C, clip)
    t.wf32(clip + 0x0C, edge(t))
    t.wf32(entry + 4, edge(t))
    t.wf32(entry + 0x14, edge(t))
    if t.index % 7 == 0:
        t.w32(replay + 0x68CF0, 0)
        t.wf32(t.sym("g_sysTimeManager") + 8, 0.25)
        t.wf32(clip + 0x0C, 1.0)
        t.wf32(entry + 4, 1.0)
        t.wf32(entry + 0x14, t.rng.choice([0.0, 0.5, 0.75, 1.0]))
    t.args(r3=entry)
