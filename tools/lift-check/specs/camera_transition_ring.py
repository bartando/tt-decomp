"""Time scan then mode/predicate scan, wraparound, empty rings and rereads."""
from liftcheck.spec import *
FUNCTION = "pongCameraMgr_6E08"
ADDRESS = 0x82216E08
SOURCE = "src/game/camera/pong_camera_helpers.cpp"
TRIALS = 512

def predicate(ctx):
    entry = ctx.r(3)
    ctx.write(entry, ctx.read(entry + 12, 4))
    ctx.ret(r3=int((int.from_bytes(ctx.read(entry + 4, 4), "big") & 255) != 0))

CALLS = {"pongCameraMgr_5CE8": model(predicate, args=("r3", "r4", "r5"),
                                    deref={"r3": 20}, preserves=("r5", "f11"))}
# The original predicate never writes r5 or f11. Its callers retain the
# required-condition count and the clamp bound in those registers.

def inputs(t):
    ring = t.alloc(32, "transition ring")
    entries = t.alloc(8 * 20, "transitions")
    key = t.alloc(16, "key")
    flags = t.alloc(32, "flags") if t.index % 3 else 0
    head = t.rng.randrange(8)
    end = (head + t.rng.randrange(8)) % 8
    mode = t.rng.choice([0, 3, 6, -1])
    t.w32(ring + 12, entries)
    t.w32(ring + 16, end)
    t.w32(ring + 24, head)
    t.w32(ring + 28, 8)
    t.wf32(key, t.rng.choice([-10., 0., 10., float("nan")]))
    for i in range(8):
        entry = entries + i * 20
        t.wf32(entry, t.rng.choice([-11., -1., 0., 1., 11., float("nan")]))
        t.w32(entry + 4, t.rng.choice([0, 0x100, 1, 2, 255, 0x12340001]))
        t.w32(entry + 8, t.rng.choice([mode, mode, mode ^ 1]))
        t.wf32(entry + 12, t.rng.uniform(-100, 100))
    t.args(r3=ring, r4=key, r5=mode, r6=flags, r7=t.rng.choice([-1, 0, 1, 4]))
