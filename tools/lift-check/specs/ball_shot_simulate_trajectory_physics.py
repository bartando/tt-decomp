"""82284078 with both real original flight helpers running: spin/drag/gravity,
material friction and sphere impulse bounce integrated through both legs.
Math library boundaries and the archetype's gravity factor are modeled.
This costly real-helper variant runs48 trials (two complete24-profile passes);
the separate full-path boundary spec runs1,000 trials per seed.
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *
import _ball_shot_simulation_common as common

FUNCTION = "BallShot_SimulateTrajectory"
ADDRESS = 0x82284078
SOURCE = "src/game/ball/ball_shot_simulation.cpp"
TRIALS = 48
FP_CONTRACT = "off"
CALLS = dict(common.CALLS)
CALLS.update({
    "BallFlight_Acceleration": run(),
    "BallFlight_Bounce": run(),
    "crt_tan": model(lambda ctx: ctx.ret(f1=math.tan(ctx.f(1)))),
    "crt_sqrt": model(lambda ctx: ctx.ret(f1=math.sqrt(ctx.f(1)))),
    "arch.vfn_12": stub(ret=1.0),
})


def inputs(t):
    common.inputs(t)
    # Canonical nonnegative physical drag; the boundary-model spec separately
    # varies this shared scalar as the table-edge clearance.
    t.wf32(0x825C8078, .01)
