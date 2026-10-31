"""Quaternion angular distance: fused dot order, abs, strict bounds, NaNs and unit pairs."""
import math
from liftcheck.spec import *

FUNCTION = "BallPredict_QuaternionAngle"
ADDRESS = 0x82137BF8
SOURCE = "src/game/ball/ball_prediction_quaternion.cpp"
TRIALS = 1200

CALLS = {
    "crt_acos": run(),
    0x82430BA8: run(args=("r4", "f1")),
}


def unit(rng):
    q = [rng.uniform(-1, 1) for _ in range(4)]
    norm = math.sqrt(sum(v * v for v in q))
    return [v / norm for v in q]


def inputs(t):
    rng = t.rng
    first = t.alloc(16, "first quaternion", floats=[(0, 4)])
    second = t.alloc(16, "second quaternion", floats=[(0, 4)])
    mode = t.index % 12
    a, b = unit(rng), unit(rng)
    if mode == 0:
        b = a[:]
    elif mode == 1:
        b = [-v for v in a]
    elif mode in (2, 3, 4, 5, 6, 7):
        a = [1., 0., 0., 0.]
        b = [[-1., 0., 0., 0.], [1., 0., 0., 0.], [-1.00001, 0., 0., 0.],
             [1.00001, 0., 0., 0.], [-0.99999, 0., 0., 0.], [0.99999, 0., 0., 0.]][mode - 2]
    elif mode == 8:
        a = [0., -0., 0., -0.]
    elif mode == 9:
        a[rng.randrange(4)] = float("nan")
    elif mode == 10:
        a[rng.randrange(4)] = rng.choice([float("inf"), -float("inf"), 1e-40, -1e-40])
    elif mode == 11:
        a, b = [rng.uniform(-2, 2) for _ in range(4)], [rng.uniform(-2, 2) for _ in range(4)]
    for p, q in ((first, a), (second, b)):
        for i, v in enumerate(q):
            t.wf32(p + 4 * i, v)
    t.args(r3=first, r4=rng.choice([first, second]))
