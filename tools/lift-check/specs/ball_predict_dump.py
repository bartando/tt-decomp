"""Prediction diagnostics distinguish all table contacts from elapsed contacts."""
from liftcheck.spec import *
FUNCTION = "BallPredict_Dump"
ADDRESS = 0x821D9238
SOURCE = "src/game/ball/ball_prediction_queries.cpp"
TRIALS = 800
CALLS = {
    "nop_8240E6D0": stub(ret="void",args=("r3","r4","r5")),
    "gdBallPredictData::CountBouncesSoFar": run(),
}


def inputs(t):
    r=t.rng
    data=t.alloc(0x2800,"prediction",ctype="gdBallPredictData")
    n=r.choice([-1,0,1,2,3,8,10])
    t.w32(data+0x27E0,n)
    for i in range(max(0,n)):
        t.wf32(data+0x2790+8*i,r.choice([-2.0,0.0,1.0,2.0,4.0]))
        t.w8(data+0x2794+8*i,r.choice([0,0,1,2,0x80]))
    clock=t.alloc(0x40,"match clock")
    t.wf32(clock+0x30,r.choice([-2.0,0.0,1.0,2.0,4.0]))
    t.w32(0x8271A2E8,clock)
    t.args(r3=data)
