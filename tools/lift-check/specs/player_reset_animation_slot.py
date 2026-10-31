"""0x820D6D48: reset the slot state without overwriting basis w lanes/gaps."""
from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_6D48"
ADDRESS = 0x820D6D48
SOURCE = "src/game/player/player_animation_reset_helpers.cpp"
TRIALS = 1000
EXTERNS = {"lbl_825C5938": 0x825C5938}


def clear_base(ctx):
    ctx.write(ctx.r(3), ctx.rng.randbytes(0x80))


CALLS = {"LocomotionStateAnim::ResetAccumulators": model(clear_base)}


def inputs(t):
    obj = t.alloc(0x150, "slot")
    t.wf32(t.sym("lbl_825C5938"), t.rng.uniform(-3, 3))
    t.args(r3=obj)
