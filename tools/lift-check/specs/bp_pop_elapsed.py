"""gdBallPredictData::PopElapsed (0x821D7840): drop samples game time has passed,
reporting each to the replay recorder and the pop callback."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import predict_data, logical, EXTERNS  # noqa: F401

FUNCTION = "gdBallPredictData::PopElapsed"
ADDRESS = 0x821D7840
SOURCE = "src/game/ball/ball_predict.cpp"

_scratch = {}


def _record(ctx):
    # The record leaves 8 bytes unwritten; copy the rest where the memory diff sees it.
    data = ctx.read(ctx.r(4), 0x30)
    k = _scratch.setdefault(ctx.side, 0)
    _scratch[ctx.side] = k + 1
    if k < 16:
        ctx.write(_scratch["addr"] + 0x28 * k, bytes(data[0:8]) + bytes(data[16:48]))


CALLS = {
    0x821CD0F8: model(_record),
    0x8225FFF8: stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    d, tail, count = predict_data(t, sorted_times=True)
    _scratch.clear()
    _scratch["addr"] = t.alloc(0x28 * 16, "records", fill="zero")

    timing = t.alloc(0x40, "timing")
    t0 = rng.uniform(0.0, 7.0)
    t.wf32(timing + 0x30, t0)
    t.w32(0x8271A2E8, timing)

    flag = t.alloc(4, "replayPlaying")
    t.w32(flag, rng.choice([0, 0, 1]))
    t.w32(0x8271A2EC, (flag - 0x68CF0) & 0xFFFFFFFF)

    t.wf32(d + 0x2604, rng.choice([-1.0, rng.uniform(0.0, 7.0)]))
    t.w32(d + 0x27F4, rng.choice([0, 0, 1, 0x82000000]))
    t.args(r3=d, r4=rng.choice([0, 1]))
