"""Reset both records, retaining the header and every untouched padding byte."""
from liftcheck.spec import *
FUNCTION = "fxBallSplash2D_ResetSplashes"
ADDRESS = 0x82389BD8
SOURCE = "src/game/ball/ball_splash.cpp"
TRIALS = 256

def inputs(t):
    t.args(r3=t.alloc(0xD0, "splash"))
