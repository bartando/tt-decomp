"""Indexed insert: append-last, backward shifts/unrolled boundaries, source aliases."""
from specs._ball_replay_common import *
from liftcheck.spec import *

FUNCTION = "BallReplay_InsertSample"
ADDRESS = 0x821CF298
SOURCE = "src/game/ball/ball_replay.cpp"
TRIALS = 800


def inputs(t):
    q, tail, count, times = make_queue(t)
    sample = make_sample(t)
    index = t.rng.choice([0, max(0, count - 1), t.rng.randrange(max(1, count))])
    if count > 1 and t.index % 9 == 0:
        index = -1  # unordered-time caller can leave its neighbor index at -1
    sample = t.rng.choice([sample, sample, logical(q, tail, max(0, count - 1)),
                           logical(q, tail, max(0, index)), q + t.rng.randrange(900) * SAMPLE])
    t.args(r3=q, r4=index, r5=sample)
