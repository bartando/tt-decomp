"""Shared replay-ring input builders and real-call policies."""
import struct
from liftcheck.spec import run, stub

CAPACITY = 900
SAMPLE = 0x30
HEAD = 0xA8C0
TAIL = 0xA8C4
COUNT = 0xA8C8
SIZE = 0xA8D0

CALLS = {
    "BallReplay_AppendSample": run(),
    "BallReplay_FindNeighborIndices": run(args=("r3", "r5", "r6", "r7", "f1")),
    "BallReplay_InsertSample": run(),
    "BallReplay_InsertTimedSample": run(),
    "rage_debugLog": stub(ret="void", args=("r3",)),
}


def logical(queue, tail, i):
    return queue + ((tail + i + 1) % CAPACITY) * SAMPLE


def fill_queue(t, queue, count, tail):
    rng = t.rng
    t.w32(queue + HEAD, (tail + count) % CAPACITY)
    t.w32(queue + TAIL, tail)
    t.w32(queue + COUNT, count)
    times = []
    clock = -5.
    for i in range(CAPACITY):
        clock += rng.choice([0., 0., 0.125, 0.5, 1.])
        p = logical(queue, tail, i)
        t.wf32(p, clock)
        t.wf32(p + 4, rng.uniform(-10, 10))
        times.append(struct.unpack(">f", struct.pack(">f", clock))[0])
    return times


def make_queue(t, count=None, tail=None, name="replay queue"):
    rng = t.rng
    if count is None:
        count = 900 if t.index % 61 == 0 else 899 if t.index % 61 == 1 else rng.choice([0, 1, 2, 3, 5, 8, 9, 20, 31, 63])
    if tail is None:
        tail = rng.choice([0, 1, 898, 899, rng.randrange(CAPACITY)])
    queue = t.alloc(SIZE, name)
    times = fill_queue(t, queue, count, tail)
    return queue, tail, count, times


def make_sample(t, name="incoming sample"):
    p = t.alloc(SAMPLE, name)
    t.wf32(p, t.rng.uniform(-10, 10))
    t.wf32(p + 4, t.rng.uniform(-10, 10))
    return p


def query_time(t, count, times):
    last = max(0, count - 1)
    return t.rng.choice([times[0] - 1., times[0], times[last], times[last] + 1.,
                          times[t.rng.randrange(max(1, count))],
                          (times[0] + times[last]) * 0.5,
                          float("nan"), float("inf"), -float("inf")])
