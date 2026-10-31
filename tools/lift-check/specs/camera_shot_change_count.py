"""Counter snapshots, interval-end copy, late time read and near/far branches."""
from liftcheck.spec import *
FUNCTION = "pg_7CD8_2h"
ADDRESS = 0x821F7CD8
SOURCE = "src/game/camera/pong_camera_helpers.cpp"
TRIALS = 512

def interval(ctx):
    state, key = ctx.r(3), ctx.r(4)
    ctx.write(key, ctx.read(state, 8))
    ctx.write(0x826064c4, ctx.read(state + 20, 4))
    ctx.ret(r3=ctx.read(state + 16, 1)[0])

def clamp(ctx):
    key, state = ctx.r(3), ctx.r(4)
    ctx.write(key, ctx.read(state + 8, 8))
    ctx.write(0x826064c4, ctx.read(state + 24, 4))
    ctx.ret(r3=ctx.read(state + 17, 1)[0])

CALLS = {
    "pg_6F68": model(interval, args=("r3", "r4", "r5", "r6", "r7"), deref={"r4": 8}),
    "pongCameraMgr_3500_fw": model(clamp, args=("r3", "r4", "r5"), deref={"r3": 8}, preserves=("f9",)),
}
# 3500 and both real callees only use f0/f10/f11/f12/f13, leaving f9 intact.

def inputs(t):
    key = t.alloc(8, "source key")
    state = t.alloc(32, "query script")
    vals = [-1., -0., 0., .0005, .001, .002, 1., float("inf"), float("nan")]
    t.wf32(key, t.rng.choice(vals))
    t.wf32(key + 4, t.rng.choice(vals))
    t.wf32(state, t.rng.choice(vals))
    t.wf32(state + 8, t.rng.choice(vals))
    t.w8(state + 16, t.index % 2)
    t.w8(state + 17, (t.index // 2) % 2)
    count = t.rng.choice([0, 1, 2, 3, 6, -1, -2147483648])
    t.w32(0x826064c4, (count - t.rng.randrange(4)) & 0xffffffff)
    t.wf32(0x825c5ebc, t.rng.choice([-1., -0., 0., 1., float("nan")]))
    if t.index < 384:
        # Cartesian cases guarantee both near/far accepted counts, the exact
        # epsilon boundary and unordered distance, for every query outcome.
        pairs = [(0., 0.), (.0005, 0.), (.001, 0.), (.002, 0.),
                 (float("nan"), 0.), (1., float("inf"))]
        current, result = pairs[(t.index // 4) % len(pairs)]
        t.wf32(state, current)
        t.wf32(state + 8, result)
        t.w32(0x826064c4, (count - ((t.index // 24) % 4)) & 0xffffffff)
        t.wf32(0x825c5ebc, [1., 0., -1., float("nan")][t.index // 96])
    t.args(r3=key, r4=state, r5=t.rng.getrandbits(32), r6=t.rng.getrandbits(32), r7=count)
