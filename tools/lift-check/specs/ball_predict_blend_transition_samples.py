"""Transition blend: fused clocks and X/Z, first Y, untouched W, carried velocity/flags,
shortest-hemisphere quaternion input, aliases and preserved padding."""
from liftcheck.spec import *

FUNCTION = "BallPredict_BlendTransitionSamples"
ADDRESS = 0x821D7460
SOURCE = "src/game/ball/ball_prediction_stream.cpp"
TRIALS = 1400


def slerp(c):
    # Make every quaternion lane observable without duplicating the math callee.
    c.write(c.r(3), c.read(c.r(5), 16))


CALLS = {
    "BallPredict_QuaternionSlerp": model(slerp, args=("r3", "r5", "r6", "f1"),
                                        deref={"r5": 16, "r6": 16}),
}


def inputs(t):
    rng = t.rng
    first = t.alloc(0x50, "first", ctype="gdBallPredictSample")
    second = t.alloc(0x50, "second", ctype="gdBallPredictSample")
    output = t.alloc(0x50, "output", ctype="gdBallPredictSample")
    special = [0., -0., 1e-40, -1e-40, 1., -1., float("nan"), float("inf"), -float("inf")]
    for p in (first, second):
        for off in (0, 4, *range(0x10, 0x50, 4)):
            val = rng.choice(special) if t.index % 4 == 0 else rng.uniform(-10, 10)
            t.wf32(p + off, val)
        for off in (8, 9, 10):
            t.w8(p + off, rng.choice([0, 0, 1, 2, 0x80, 0xff]))
    factor = rng.choice(special) if t.index % 4 == 0 else rng.uniform(-0.25, 1.25)
    output = rng.choice([output, output, output, first, second])
    t.args(r3=output, r4=rng.getrandbits(32), r5=first, r6=second, f1=factor)
