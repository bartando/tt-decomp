"""gdBallPredictData::BuildBounceList (0x821D90B8)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403
from _bp_common import predict_data, sparse_bounces, zero_stack_fill, EXTERNS as _E

FUNCTION = "gdBallPredictData::BuildBounceList"
ADDRESS = 0x821D90B8
SOURCE = "src/game/ball/ball_predict.cpp"
EXTERNS = dict(_E, g_input_obj_ptr=0x825EAB28)
CALLS = {0x821D93F0: run()}


def inputs(t):
    rng = t.rng
    zero_stack_fill(t)
    d, tail, count = predict_data(t)
    sparse_bounces(t, d, tail, count)
    t.w32(d + 0x27E0, rng.randrange(0, 3))
    t.w8(d + 0x27E4, rng.choice([0, 1, 1]))
    inp = t.alloc(0x44, "input")
    t.w8(inp + 0x40, rng.choice([0, 1, 2]))
    t.w32(0x825EAB28, inp)
    t.args(r3=d, r4=t.rng.choice([0, 1]))
