"""Bounds arguments, input rereads, factors and returned embedded position."""
from liftcheck.spec import *
FUNCTION = "pongPlayer_E7B0_g"
ADDRESS = 0x8219E7B0
SOURCE = "src/game/player/player_court.cpp"
TRIALS = 256

def bounds(ctx):
    table = ctx.r(3)
    target = int.from_bytes(ctx.read(table, 4), "big")
    ctx.write(target, ctx.read(table + 4, 12))
    ctx.write(ctx.r(5), ctx.read(table + 16, 12))
    ctx.write(ctx.r(6), ctx.read(table + 28, 12))
    ctx.ret(r3=table)

def interpolate(ctx):
    ctx.write(ctx.r(5), ctx.read(0x82606720, 16))
    ctx.ret()

CALLS = {
    "pongPlayer_GetCourtBounds": model(bounds, args=("r3", "r4", "r5", "r6", "r7", "r8")),
    "pongPlayer_InterpolateCourtGridPosition": model(interpolate,
        args=("r4", "r8"), deref={"r3": 8, "r6": 12, "r7": 12}, preserves=("r5",)),
}

def inputs(t):
    target = t.alloc(32, "cell")
    table = t.alloc(48, "table script")
    t.w32(table, target)
    t.w32(0x8271a304, table)
    t.args(r3=target)
