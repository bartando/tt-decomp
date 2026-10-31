"""Replay recording: evict oldest when full, wrap tail and use the real sorted insert."""
from specs._ball_replay_common import *
from liftcheck.spec import *

FUNCTION = "gdReplayMgr_RecordBallSample"
ADDRESS = 0x821CD0F8
SOURCE = "src/game/ball/ball_replay.cpp"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    replay = t.alloc(0x4020 + SIZE, "replay manager")
    q = replay + 0x4020
    count = 900 if t.index % 61 in (0, 3) else 899 if t.index % 61 == 1 else rng.choice([0, 1, 2, 3, 9, 20, 31, 63])
    tail = 899 if t.index % 61 == 3 else rng.choice([0, 1, 898, 899, rng.randrange(900)])
    times = fill_queue(t, q, count, tail)
    sample = make_sample(t)
    t.wf32(sample, query_time(t, count, times))
    if count and t.index % 4 == 0:
        sample = logical(q, tail, rng.randrange(count))
    t.args(r3=replay, r4=sample)
