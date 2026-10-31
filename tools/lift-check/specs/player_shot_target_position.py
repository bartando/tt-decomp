"""Cached full vector or live aim/bounds/ball-radius reconstruction.

The recompute path's original stack temporary initializes only xyz. Ignore
its padding w in that path; cached-path w and every other byte are checked.
"""
from liftcheck.spec import *
FUNCTION = "pongPlayer_ComputeTargetPosition"
ADDRESS = 0x821D6470
SOURCE = "src/game/player/player_shot_position.cpp"
TRIALS = 512

def bounds(ctx):
    table = ctx.r(3)
    entry = int.from_bytes(ctx.read(table, 4), "big")
    ctx.write(ctx.r(5), ctx.read(table + 0x30, 12))
    ctx.write(ctx.r(6), ctx.read(table + 0x40, 12))
    ctx.write(entry + 0x100, ctx.read(table + 8, 8))
    ctx.write(entry + 0xd6, ctx.read(table + 0x28, 1))
    ctx.ret(r3=table)

CALLS = {"pongPlayer_GetCourtBounds": model(bounds, args=("r3", "r4", "r5", "r6", "r7", "r8"))}

def inputs(t):
    entry = t.alloc(0x180, "shot entry")
    output = t.rng.choice([t.alloc(16, "output"), entry + 0x100, entry + 0x120])
    table = t.alloc(0x50, "court and bounds script")
    root = t.alloc(4, "ball slot")
    ball = t.alloc(8, "ball")
    body = t.alloc(16, "body")
    shape = t.alloc(16, "shape")
    t.w32(0x8271a304, table)
    t.w32(0x8271a2f4, root)
    t.w32(root, t.rng.choice([0, ball]))
    t.w32(ball + 4, body)
    t.w32(body + 12, shape)
    t.w32(table, entry)
    values = [-1., -0., 0., 1., 2., float("inf"), -float("inf"), float("nan")]
    for p in [table + 8, table + 12, table + 20, shape + 8,
              *[table + base + i * 4 for base in (0x30, 0x40) for i in range(3)]]:
        t.wf32(p, t.rng.choice(values) if t.index < 200 else t.rng.uniform(-100, 100))
    t.w8(table + 0x28, t.rng.choice([0, 1, 2, 255]))
    t.w8(entry + 0xd6, t.rng.choice([0, 1, 2, 255]))
    resolved = t.rng.choice([0, 0, 1, 2, 255])
    t.w8(entry + 0xd8, resolved)
    force = t.rng.choice([0, 1, 2, 255, 256, 0x10000])
    if not (resolved and (force & 255) == 0):
        t.ignore(output + 12, 4)
    t.args(r3=output, r4=entry, r5=force)
