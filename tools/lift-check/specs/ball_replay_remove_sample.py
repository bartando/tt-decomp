"""Replay removal: forward compaction, head wrap and exact 8-byte padding preservation."""
from specs._ball_replay_common import *
from liftcheck.spec import *

FUNCTION = "BallReplay_RemoveSample"
ADDRESS = 0x821CE910
SOURCE = "src/game/ball/ball_replay.cpp"
TRIALS = 1000


def inputs(t):
    q, tail, count, times = make_queue(t, count=900 if t.index % 61 == 0 else 899 if t.index % 61 == 1 else t.rng.choice([1, 2, 3, 8, 9, 20, 31, 63]))
    index = t.rng.choice([0, count - 1, t.rng.randrange(count)])
    t.args(r3=q, r4=index)
