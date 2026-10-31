"""900-ring neighbor search: endpoints, duplicates, wraps, empty/singleton, NaNs."""
from specs._ball_replay_common import *
from liftcheck.spec import *

FUNCTION = "BallReplay_FindNeighborIndices"
ADDRESS = 0x821CFB60
SOURCE = "src/game/ball/ball_replay.cpp"
TRIALS = 800


def inputs(t):
    q, tail, count, times = make_queue(t)
    first, second, factor = t.alloc(4, "first"), t.alloc(4, "second"), t.alloc(4, "factor", floats=[0])
    query = query_time(t, count, times)
    if t.index % 17 == 0:
        for i in range(900):
            t.wf32(q + i * SAMPLE, float("inf"))
        query = float("inf")
    if t.index % 7 == 0:
        first = q + COUNT  # legal output alias: both are int32_t
    if t.index % 11 == 0:
        second = q + TAIL
    t.args(r3=q, r4=t.rng.getrandbits(32), r5=first, r6=second, r7=factor, f1=query)
