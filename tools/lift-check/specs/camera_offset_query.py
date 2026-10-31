"""Both query results, live-source reload, and local-key edits across calls."""
import struct
from liftcheck.spec import *
FUNCTION = "pongCameraMgr_6990"
ADDRESS = 0x821F6990
SOURCE = "src/game/camera/camera_transition_queries.cpp"
TRIALS = 512

def query(ctx):
    key, state, mode = ctx.r(3), ctx.r(4), ctx.r(5)
    source = int.from_bytes(ctx.read(state, 4), "big")
    if mode == 20:
        ctx.write(source, ctx.read(state + 4, 4))
        ctx.write(key + 4, ctx.read(state + 8, 4))
        ctx.ret(r3=ctx.read(state + 12, 1)[0])
    else:
        ctx.ret(r3=ctx.read(state + 13, 1)[0])

CALLS = {"pongCameraMgr_3500_fw": model(query, args=("r3", "r4", "r5"), deref={"r3": 8})}

def inputs(t):
    source = t.alloc(16, "source key")
    state = t.alloc(32, "evaluator")
    t.wf32(source, t.rng.uniform(-10, 10))
    t.w32(state, source)
    t.wf32(state + 4, t.rng.uniform(-10, 10))
    t.w8(state + 12, t.index % 2)
    t.w8(state + 13, (t.index // 2) % 2)
    t.wf32(0x8202D108, t.rng.choice([1., -1., 0., .25]))
    t.args(r3=source, r4=state)
