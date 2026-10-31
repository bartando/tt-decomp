"""Both 3x3 grids, all four corners, profile metadata and mirror updates.

Interpolate's output padding lane is defined by the model; only xyz of its
input offsets are compared (the original zero-offset's w is uninitialized).
"""
from liftcheck.spec import *
FUNCTION = "pongPlayer_E008_g"
ADDRESS = 0x8219E008
SOURCE = "src/game/player/player_court.cpp"
TRIALS = 128

def bounds(ctx):
    table = ctx.r(3)
    ctx.write(ctx.r(5), ctx.read(table, 12))
    ctx.write(ctx.r(6), ctx.read(table + 16, 12))
    ctx.ret(r3=table)

def interpolate(ctx):
    import struct
    values = [ctx.rng.uniform(-100, 100) for _ in range(4)]
    ctx.write(ctx.r(5), struct.pack(">4f", *values))
    ctx.ret()

CALLS = {
    "pongPlayer_GetCourtBounds": model(bounds, args=("r3", "r4", "r5", "r6", "r7", "r8"), preserves=("r4",)),
    "pongPlayer_InterpolateCourtGridPosition": model(interpolate,
        args=("r4",), deref={"r3": 8, "r6": 12, "r7": 12, "r8": 12}, preserves=("r4",)),
}

def inputs(t):
    target = t.alloc(0xc00, "target grids")
    table = t.alloc(32, "bounds script")
    t.w32(0x8271a304, table)
    t.wf32(0x825c806c, t.rng.choice([1./3., 0., -1., 1.]))
    t.args(r3=target, r4=t.rng.getrandbits(32), r5=t.rng.getrandbits(32), r6=t.rng.choice([0, 1, 2, 255, 256, -1]))
