"""gdBallPredictData::FindNearestHittableSample (0x821D8298): closest sample (3D) to a
target inside the first run of hittable, non-contact samples."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import predict_data, EXTERNS  # noqa: F401

FUNCTION = "gdBallPredictData::FindNearestHittableSample"
ADDRESS = 0x821D8298
SOURCE = "src/game/ball/ball_predict.cpp"
CALLS = {
    0x821D8990: run(),
    0x821D8A30: run(),
    0x8240E6D0: stub(ret="void", args=("r1",)),  # no-op logger; its 82-char message compares as a raw pointer
}


def inputs(t):
    d, _, _ = predict_data(t)
    tgt = t.alloc(0x50, "target")
    t.floats(tgt + 0x10, 4, -5.0, 5.0)
    out = t.alloc(4, "out")
    t.args(r3=d, r4=tgt, r5=out)
