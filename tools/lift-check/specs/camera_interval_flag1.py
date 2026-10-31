from liftcheck.spec import *
FUNCTION = "pg_3B28_fw"
ADDRESS = 0x821F3B28
SOURCE = "src/game/camera/pong_camera_helpers.cpp"
TRIALS = 256

def query(ctx):
    evaluator, key = ctx.r(3), ctx.r(4)
    ctx.write(key, ctx.read(evaluator, 8))
    ctx.ret(r3=ctx.read(evaluator + 8, 1)[0])

CALLS = {"pg_6F68": model(query, args=("r3", "r4", "r5", "r6", "r7"), deref={"r4": 8, "r6": 8})}

def inputs(t):
    key = t.alloc(8, "key")
    evaluator = t.alloc(16, "evaluator")
    t.w8(evaluator + 8, t.rng.choice([0, 1]))
    t.args(r3=key, r4=evaluator)
