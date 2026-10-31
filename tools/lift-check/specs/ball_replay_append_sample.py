"""48-byte replay append: head wrap, exact full gate, aliases and untouched padding."""
from specs._ball_replay_common import *
from liftcheck.spec import *

FUNCTION = "BallReplay_AppendSample"
ADDRESS = 0x821CF1F8
SOURCE = "src/game/ball/ball_replay.cpp"
TRIALS = 800


def inputs(t):
    q, tail, count, times = make_queue(t, count=t.rng.choice([-1, 0, 1, 2, 899, 900, 901]))
    sample = make_sample(t)
    sample = t.rng.choice([sample, sample, q + t.rng.randrange(900) * SAMPLE,
                           q + ((tail + count + 1) % 900) * SAMPLE])
    t.args(r3=q, r4=sample)
