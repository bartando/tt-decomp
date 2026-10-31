"""0x82280358: finite xyz exponent fields, preserving ignored w semantics."""
from liftcheck.spec import *
FUNCTION = "BallPredict_IsFiniteXYZ"
ADDRESS = 0x82280358
SOURCE = "src/game/ball/ball_prediction_outcome_helpers.cpp"
TRIALS = 800


def inputs(t):
    vector = t.alloc(16, "vector")
    choices = [0, 0x80000000, 1, 0x007FFFFF, 0x7F7FFFFF, 0xFF7FFFFF,
               0x7F800000, 0xFF800000, 0x7FC00000, 0xFFC12345]
    for i in range(4):
        t.w32(vector + i * 4, t.rng.choice(choices))
    if t.index % 4 == 0:
        for i in range(3):
            t.wf32(vector + 4 * i, 1.0)
        t.w32(vector + 12, 0x7F800000)
    t.args(r3=vector)
