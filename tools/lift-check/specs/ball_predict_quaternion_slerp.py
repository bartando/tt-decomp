"""Quaternion spherical interpolation, singular copy, extrapolation, NaNs,
whole-object aliases, normalization and surrounding memory guards."""
import math
from liftcheck.spec import *

FUNCTION = "BallPredict_QuaternionSlerp"
ADDRESS = 0x8223AED0
SOURCE = "src/game/ball/ball_prediction_quaternion.cpp"
TRIALS = 1400

CALLS = {
    "BallPredict_QuaternionAngle": run(),
    "crt_acos": run(),
    0x82430BA8: run(args=("r4", "f1")),
    "crt_sin": run(),
    "rage::NormalizeQuaternion": run(),
}


def unit(rng):
    q = [rng.uniform(-1, 1) for _ in range(4)]
    norm = math.sqrt(sum(v * v for v in q))
    return [v / norm for v in q]


def inputs(t):
    rng = t.rng
    storage = t.alloc(112, "quaternions and guards")
    first, second, out = storage + 16, storage + 48, storage + 80
    for p in (first, second, out):
        t.mark_type(p, "bpVec4")
    a, b = unit(rng), unit(rng)
    mode = t.index % 12
    if mode == 0:
        a, b = [0., 0., 0., 1.], [0., 0., 0., 1.]
    elif mode == 1:
        b = a[:]
    elif mode == 2:
        b = [-v for v in a]
    elif mode == 3:
        a, b = [0., -0., 0., -0.], [0., 0., 0., 1.]
    elif mode == 4:
        angle = rng.uniform(1e-5, 1e-3)
        a, b = [0., 0., 0., 1.], [math.sin(angle), 0., 0., math.cos(angle)]
    elif mode == 5:
        a[rng.randrange(4)] = float("nan")
    elif mode == 6:
        b[rng.randrange(4)] = rng.choice([float("inf"), -float("inf"), 1e-40, -1e-40])
    elif mode == 7:
        a, b = [rng.uniform(-2, 2) for _ in range(4)], [rng.uniform(-2, 2) for _ in range(4)]
    for p, q in ((first, a), (second, b)):
        for i, v in enumerate(q):
            t.wf32(p + 4 * i, v)
    second = rng.choice([first, second, second, second])
    out = rng.choice([out, out, first, second])
    factor = rng.choice([0., -0., 0.125, 0.5, 1., -0.5, 1.5, rng.uniform(0, 1)])
    if mode == 10:
        factor = float("nan")
    t.args(r3=out, r4=rng.getrandbits(32), r5=first, r6=second, f1=factor)
