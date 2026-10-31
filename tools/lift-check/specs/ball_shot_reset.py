"""0x821D51C8: full initialized vectors and retained scalar/vector holes."""
from liftcheck.spec import *
FUNCTION = "bpShot_Reset"
ADDRESS = 0x821D51C8
SOURCE = "src/game/ball/ball_shot_initialize.cpp"
TRIALS = 512
EXTERNS = {"g_floatConstant4": 0x825C7600}

def inputs(t):
    shot = t.alloc(0xc0, "shot", ctype="bpShot")
    t.wf32(0x825c7600, t.rng.choice([-1., 0., 1., 4., 100., float("nan")]))
    t.args(r3=shot)
