"""gdBallPredictSample::operator= (0x820D6E58): field copy that skips the padding."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import fill_sample

FUNCTION = "gdBallPredictSample::operator="
ADDRESS = 0x820D6E58
SOURCE = "src/game/ball/ball_predict.cpp"


def inputs(t):
    dst = t.alloc(0x50, "dst", ctype="gdBallPredictSample")
    src = t.alloc(0x50, "src", ctype="gdBallPredictSample")
    fill_sample(t, src)
    t.args(r3=dst, r4=src)
