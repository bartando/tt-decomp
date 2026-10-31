"""Ring time neighbors, clipped endpoints, duplicates, empty/singleton and unordered input."""
from liftcheck.spec import *

FUNCTION = "BallPredict_FindNeighborIndices"
ADDRESS = 0x821D96A0
SOURCE = "src/game/ball/ball_prediction_stream.cpp"
TRIALS = 1200
CALLS = {"rage_debugLog": stub(ret="void", args=("r3",))}


def inputs(t):
    rng = t.rng
    ring = t.alloc(0x2590, "sample ring")
    tail = rng.randrange(120)
    count = rng.choice([0, 1, 2, 3, 8, 119, 120])
    t.w32(ring + 0x2584, tail)
    t.w32(ring + 0x2588, count)
    times = []
    time = rng.uniform(-4, 4)
    for i in range(120):
        time += rng.choice([0, 0.01, 0.125, 1., 4.])
        times.append(time)
        t.wf32(ring + ((tail + i + 1) % 120) * 0x50, time)
    n = max(0, count - 1)
    query = rng.choice([times[0] - 1, times[0], times[n], times[n] + 1,
                        rng.uniform(times[0], times[n]), float("nan")])
    # Infinities and malformed internal times exercise the original's no-span return.
    if t.index % 11 == 0:
        for i in range(120):
            t.wf32(ring + i * 0x50, float("inf"))
        query = float("inf")
    elif t.index % 13 == 0 and count > 2:
        for i in range(count):
            t.wf32(ring + ((tail + i + 1) % 120) * 0x50, rng.choice([0., 1., float("nan")]))
        query = 0.5
    first = t.alloc(4, "first index")
    second = t.alloc(4, "second index")
    factor = t.alloc(4, "lerp factor", floats=[0])
    t.args(r3=ring, r4=rng.getrandbits(32), r5=first, r6=second, r7=factor, f1=query)
