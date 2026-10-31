"""0x821D5128: partial shot initialization with all padding/w lanes preserved."""
from liftcheck.spec import *
FUNCTION = "ballPredict_InitialiseShot"
ADDRESS = 0x821D5128
SOURCE = "src/game/ball/ball_shot_initialize.cpp"
TRIALS = 400
EXTERNS = {"g_floatConstant4": 0x825C7600}
def inputs(t):
    shot = t.alloc(0xC0,'shot',ctype='bpShot')
    t.wf32(t.sym('g_floatConstant4'),t.rng.uniform(-100,100))
    t.args(r3=shot)
