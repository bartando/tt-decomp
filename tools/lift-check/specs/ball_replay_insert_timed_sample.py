"""Sorted replay insert: before/equal/after times, duplicates, NaNs, source aliases."""
from specs._ball_replay_common import *
from liftcheck.spec import *

FUNCTION = "BallReplay_InsertTimedSample"
ADDRESS = 0x821CE780
SOURCE = "src/game/ball/ball_replay.cpp"
TRIALS = 1000


def inputs(t):
    q, tail, count, times = make_queue(t, count=1 if t.index % 20 == 1 else 3 if t.index % 20 == 2 else None)
    sample = make_sample(t)
    query = query_time(t, count, times)
    if t.index % 20 == 1:
        query = float("nan")
    elif t.index % 20 == 2:
        for i, value in enumerate([1., 1., 2.]):
            t.wf32(logical(q, tail, i), value)
        query = 1.
    t.wf32(sample, query)
    if count and t.index % 4 == 0:
        sample = logical(q, tail, t.rng.randrange(count))
    t.args(r3=q, r4=sample)
