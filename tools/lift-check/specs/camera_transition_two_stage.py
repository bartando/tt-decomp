"""Two bounds checks and an atomic source commit; second-word edits survive."""
from liftcheck.spec import *
FUNCTION = "pongCameraMgr_7338_helper"
ADDRESS = 0x821F7338
SOURCE = "src/game/camera/pong_camera_helpers.cpp"
TRIALS = 512

def first(ctx):
    state, key = ctx.r(3), ctx.r(4)
    ctx.write(key, ctx.read(state, 8))
    ctx.ret(r3=ctx.read(state + 16, 1)[0])

def second(ctx):
    state, key = ctx.r(3), ctx.r(4)
    ctx.write(key, ctx.read(state + 8, 8))
    ctx.ret(r3=ctx.read(state + 17, 1)[0])

CALLS = {
    "pongCameraMgr_6E08": model(first, args=("r3", "r4", "r5", "r6", "r7"), deref={"r4": 8, "r6": 8}),
    "pg_6F68": model(second, args=("r3", "r4", "r5", "r6", "r7"), deref={"r4": 8, "r6": 8}),
}

def inputs(t):
    source = t.alloc(8, "source")
    state = t.alloc(24, "evaluator")
    vals = [-10., 0., 10., -0., float("nan"), float("inf"), -float("inf")]
    for p in [source, 0x825C5EC0, state, state + 8]:
        t.wf32(p, t.rng.choice(vals))
    t.w8(state + 16, t.index % 2)
    t.w8(state + 17, (t.index // 2) % 2)
    t.args(r3=source, r4=state, f1=t.rng.random(), f2=t.rng.random())
