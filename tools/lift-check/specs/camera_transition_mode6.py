"""Exact eight-byte snapshot, mode/flags, bounds, NaNs and partial writes."""
import struct
from liftcheck.spec import *
FUNCTION = "pongCameraMgr_5308_fw"
ADDRESS = 0x821F5308
SOURCE = "src/game/camera/camera_transition_queries.cpp"
TRIALS = 512

def transition(ctx):
    state, key = ctx.r(3), ctx.r(4)
    ctx.write(key, ctx.read(state, 8))
    ctx.ret(r3=ctx.read(state + 8, 1)[0])

CALLS = {"pongCameraMgr_6E08": model(transition, args=("r3", "r4", "r5", "r6", "r7"),
                                   deref={"r4": 8, "r6": 8}, preserves=("f11",))}
# 0x82216E08 and its only callee 0x82215CE8 write f0/f12/f13, never
# f11; this caller keeps its upper bound there across the call.

def inputs(t):
    source = t.alloc(16, "source key")
    state = t.alloc(16, "evaluator")
    vals = [-10., 0., 10., -0., float("nan"), float("inf"), -float("inf")]
    current = vals[t.index % len(vals)] if t.index < 100 else t.rng.uniform(-100, 100)
    threshold = vals[(t.index // len(vals)) % len(vals)] if t.index < 100 else t.rng.uniform(-100, 100)
    result = vals[(t.index // 3) % len(vals)] if t.index < 100 else t.rng.uniform(-100, 100)
    t.wf32(source, current)
    t.wf32(0x825C5EC0, threshold)
    t.wf32(state, result)
    t.w8(state + 8, [0, 1, 2, 255][t.index % 4])
    t.args(r3=source, r4=state)
