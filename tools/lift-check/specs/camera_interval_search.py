"""Mutable circular cursor, half-open interval, rewind and condition filter."""
from liftcheck.spec import *
FUNCTION = "pg_6F68"
ADDRESS = 0x82216F68
SOURCE = "src/game/camera/pong_camera_helpers.cpp"
TRIALS = 512

def predicate(ctx):
    entry = ctx.r(3)
    # The accepted time must be reread after the callback.
    ctx.write(entry, ctx.read(entry + 12, 4))
    ctx.ret(r3=int((int.from_bytes(ctx.read(entry + 4, 4), "big") & 255) != 0))

CALLS = {
    0x82215B10: run(transparent=True),
    0x82215BC8: run(transparent=True),
    0x820DC4E8: run(transparent=True),
    "pongCameraMgr_5CE8": model(predicate, args=("r3", "r4", "r5"), deref={"r3": 20}),
}

def inputs(t):
    ring = t.alloc(40, "evaluator")
    entries = t.alloc(8 * 20, "entries")
    key = t.alloc(8, "interval key")
    flags = t.alloc(32, "flags") if t.index % 3 else 0
    head = t.rng.randrange(8)
    end = t.rng.randrange(8)
    count = t.rng.choice([-1, 0, 1, 2, 8])
    mode = t.rng.choice([0, 3, 5, 6, -1])
    t.w32(ring + 8, count)
    t.w32(ring + 12, entries)
    t.w32(ring + 16, end)
    t.w32(ring + 24, head)
    t.w32(ring + 28, 8)
    t.w32(ring + 32, t.rng.randrange(8))
    t.w32(ring + 36, 8)
    t.wf32(key, t.rng.choice([-10., 0., 1., 10., float("nan")]))
    t.wf32(key + 4, t.rng.choice([-1., 0., 1., 10., 20., float("inf"), float("nan")]))
    for i in range(8):
        entry = entries + i * 20
        t.wf32(entry, t.rng.choice([-11., -10., -1., 0., 1., 10., 11., float("nan")]))
        t.w32(entry + 4, t.rng.choice([0, 0x100, 1, 2, 255]))
        t.w32(entry + 8, t.rng.choice([mode, mode, mode ^ 1, 0]))
        t.wf32(entry + 12, t.rng.uniform(-100, 100))
    t.args(r3=ring, r4=key, r5=mode, r6=flags, r7=t.rng.choice([-1, 0, 1, 4]))
