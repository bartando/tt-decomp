from liftcheck.spec import *

def change(ctx):
    ctx.ret(r3=ctx.read(ctx.r(4), 1)[0])

CALLS = {"pg_7CD8_2h": model(change, args=("r3", "r4", "r7"))}
TRIALS = 128
SOURCE = "src/game/camera/pong_camera.cpp"

def inputs(t):
    key = t.alloc(8, "key")
    evaluator = t.alloc(16, "evaluator")
    t.w8(evaluator, t.rng.choice([0, 1]))
    t.args(r3=key, r4=evaluator)
