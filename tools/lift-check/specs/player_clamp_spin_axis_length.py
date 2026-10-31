"""0x821D4EA0: min/max xyz length, four-lane scale and xyz-only tiny fallback."""
from liftcheck.spec import *

FUNCTION = "pongPlayer_4EA0_g"
ADDRESS = 0x821D4EA0
SOURCE = "src/game/player/player_shot_interpolation.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def inputs(t):
    vec = t.alloc(16, "axis", floats=[(0, 4)])
    mode = t.index % 10
    values = [t.rng.uniform(-3, 3) for _ in range(4)]
    bounds = (t.rng.uniform(0, 1.5), t.rng.uniform(1.5, 3))
    if mode == 0:
        values[:3] = [0, 0, 0]
    elif mode == 1:
        values[:3] = [1.0e-7, -2.0e-7, 3.0e-7]
    elif mode == 2:
        values[:3] = [1, 0, 0]
        bounds = (1, 1)
    elif mode == 3:
        bounds = (0, 0)
    elif mode == 4:
        values[:3] = [float("nan"), 1, 0]
    elif mode == 5:
        values[:3] = [0, 0, 0]
        bounds = (0, 0)
    elif mode == 6:
        bounds = (-1, -2)
    elif mode == 7:
        values[:3] = [1.0e-40, -1.0e-40, 0]
    for lane, value in enumerate(values):
        t.wf32(vec + lane * 4, value)
    t.args(r3=vec, f1=bounds[0], f2=bounds[1])
