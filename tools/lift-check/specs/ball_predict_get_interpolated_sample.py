"""Cached ring interpolation returns its cache and preserves it for empty input."""
from liftcheck.spec import *

FUNCTION = "BallPredict_GetInterpolatedSample"
ADDRESS = 0x821D94B8
SOURCE = "src/game/ball/ball_prediction_stream.cpp"
TRIALS = 1000

CALLS = {
    "BallPredict_FindNeighborIndices": run(),
    "BallPredict_BlendSamples": run(args=("r3", "r5", "r6", "f1")),
    0x8223AED0: stub(ret="void", args=("r3", "r5", "r6", "f1"), deref={"r5": 16, "r6": 16}),
    "rage_debugLog": stub(ret="void", args=("r3",)),
}


def inputs(t):
    rng = t.rng
    ring = t.alloc(0x25E0, "ring with interpolation cache")
    tail = rng.randrange(120)
    count = rng.choice([0, 1, 2, 3, 8, 119, 120])
    t.w32(ring + 0x2584, tail)
    t.w32(ring + 0x2588, count)
    times = []
    time = -5.
    for i in range(120):
        p = ring + ((tail + i + 1) % 120) * 0x50
        time += rng.choice([0., 0.125, 1., 4.])
        times.append(time)
        t.wf32(p, time)
        t.wf32(p + 4, rng.uniform(-10, 10))
        t.floats(p + 0x10, 16, -10, 10)
        for off in (8, 9, 10):
            t.w8(p + off, rng.choice([0, 1, 2, 0x80]))
    query = rng.choice([times[0] - 1, times[0], times[max(0, count - 1)],
                        times[max(0, count - 1)] + 1,
                        rng.uniform(times[0], times[max(0, count - 1)]), float("nan")])
    t.mark_type(ring + 0x2590, "gdBallPredictSample")
    t.args(r3=ring, r4=rng.getrandbits(32), f1=query)
