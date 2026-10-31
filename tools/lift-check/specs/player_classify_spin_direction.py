"""0x821D5998: signs, y-preferred ties, zeros, NaNs, infinities and subnormals."""
from liftcheck.spec import *

FUNCTION = "fxBallSplash2D_5998_g"
ADDRESS = 0x821D5998
SOURCE = "src/game/player/player_shot_interpolation.cpp"
TRIALS = 1000
FP_CONTRACT = "off"

EDGES = [-float("inf"), -3, -1, -1.0e-40, -0.0, 0.0, 1.0e-40, 1, 3,
         float("inf"), float("nan")]


def inputs(t):
    hit = t.alloc(0x50, "hit")
    if t.index < len(EDGES) ** 2:
        x = EDGES[t.index % len(EDGES)]
        y = EDGES[t.index // len(EDGES)]
    elif t.index % 4 == 0:
        x = t.rng.uniform(-10, 10)
        y = t.rng.choice([x, -x])
    else:
        x = t.rng.uniform(-10, 10)
        y = t.rng.uniform(-10, 10)
    t.wf32(hit + 0x40, x)
    t.wf32(hit + 0x44, y)
    t.args(r3=hit)
