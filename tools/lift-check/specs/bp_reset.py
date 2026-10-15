"""gdBallPredictData::Reset (0x821D7750)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import DATA_SIZE, EXTERNS  # noqa: F401

FUNCTION = "gdBallPredictData::Reset"
ADDRESS = 0x821D7750
SOURCE = "src/game/ball/ball_predict.cpp"
CALLS = {
    0x82391510: stub(),
    0x8240E6D0: stub(ret="void", args=("r4", "r5")),  # args= compares the format as a pointer
}


def inputs(t):
    rng = t.rng
    d = t.alloc(DATA_SIZE, "predict", ctype="gdBallPredictData")
    n = rng.choice([0, 1, 3, 8])
    ids = t.alloc(max(4 * n, 4), "ids")
    t.w32(d + 0x2608, ids)
    t.w16(d + 0x260C, n)
    t.w32(0x8261A0C0, rng.getrandbits(32))
    t.args(r3=d, r4=t.alloc(8, "caller", fill=b"Caller\0\0"))
