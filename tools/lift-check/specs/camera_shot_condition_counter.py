"""Snapshot and two-phase flags, evaluator caching and live counter increment."""
from liftcheck.spec import *
FUNCTION = "pg_7818"
ADDRESS = 0x821F7818
SOURCE = "src/game/camera/pong_camera_helpers.cpp"
TRIALS = 256

def first(ctx):
    evaluator, key = ctx.r(3), ctx.r(4)
    ctx.write(key, ctx.read(evaluator, 8))
    ctx.write(0x826064C4, ctx.read(evaluator + 12, 4))
    ctx.ret(r3=ctx.read(evaluator + 8, 1)[0])

def second(ctx):
    key, evaluator = ctx.r(3), ctx.r(4)
    ctx.write(key, ctx.read(evaluator + 16, 8))
    ctx.write(0x826064C4, ctx.read(evaluator + 24, 4))
    ctx.ret(r3=ctx.read(evaluator + 9, 1)[0])

CALLS = {
    "pg_6F68": model(first, args=("r3", "r4", "r5", "r6", "r7"), deref={"r4": 8, "r6": 8}),
    "pg_3B28_fw": model(second, args=("r3", "r4"), deref={"r3": 8}),
}

def inputs(t):
    key = t.alloc(8, "source")
    replay = t.alloc(0x68D20, "replay")
    evaluator = t.alloc(32, "evaluator")
    t.w32(replay + 0x68D18, evaluator)
    t.w32(0x8271A2EC, replay)
    t.w8(evaluator + 8, t.index % 2)
    t.w8(evaluator + 9, (t.index // 2) % 2)
    t.w32(evaluator + 12, t.rng.choice([0, 1, 0xffffffff, t.rng.getrandbits(32)]))
    t.w32(evaluator + 24, t.rng.choice([0, 1, 0xffffffff, t.rng.getrandbits(32)]))
    t.args(r3=key)
