"""82284010: sign-bit crossing (including signed zero), ordered low-height
checks, optional report, and exactly the flag/height fields written."""
from liftcheck.spec import *

FUNCTION = "BallShot_RecordNetCrossing"
ADDRESS = 0x82284010
SOURCE = "src/game/ball/ball_shot_simulation.cpp"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    report = t.alloc(0x30, "report", floats=[0x24])
    current = t.alloc(16, "current", floats=[(0, 4)])
    previous = t.alloc(16, "previous", floats=[(0, 4)])
    for p in (current, previous):
        t.floats(p, 4, -2, 2)
        t.wf32(p + 4, rng.choice([-1, 0, 1, 2, float("nan")]))
        t.wf32(p + 8, rng.choice([-2, -0.0, 0.0, 2]))
    t.args(r3=report if rng.randrange(5) else 0, r4=current, r5=previous,
           f1=rng.choice([-1, 0, 1, 2, float("nan")]))
