"""0x8218BBE0: skipped groups, weight/byte propagation and live reset callbacks."""
import struct
from liftcheck.spec import *

FUNCTION = "pongPlayer_BBE0_g"
ADDRESS = 0x8218BBE0
SOURCE = "src/game/player/player_action_groups.cpp"
TRIALS = 1000


def reset(ctx):
    target = ctx.r(3)
    group, player, change = struct.unpack(">III", ctx.read(target + 4, 12))
    if change & 1:
        ctx.write(group + 8, bytes(2))
    if change & 2:
        ctx.write(player + 0x1818, bytes(2))


CALLS = {"target.vfn_1": model(reset, args=("r3",))}


def inputs(t):
    player = t.alloc(0x1820, "player")
    count = t.index % 5
    groups = t.alloc(4 * max(count, 1), "groups")
    t.w32(player + 0x1814, groups)
    t.w16(player + 0x1818, count)
    t.w32(player + 0x1CC, t.rng.choice([0, 1, 2, 3, 4, 7, -1]))
    for i in range(count):
        group = t.alloc(0x40, f"group{i}")
        t.w32(groups + i * 4, group)
        children = t.alloc(16, f"children{i}")
        child_count = t.rng.randrange(5)
        t.w32(group + 4, children)
        t.w16(group + 8, child_count)
        t.wf32(group + 0x30, t.rng.choice([0.0, -0.0, 0.5, -1.0, float("nan")]))
        t.wf32(group + 0x38, t.rng.uniform(-3, 3))
        t.w8(group + 0x3C, t.rng.choice([0, 0, 1, 0xFF]))
        t.w8(group + 0x3D, t.rng.choice([0, 0, 1, 0x80]))
        for j in range(child_count):
            child = t.alloc(16, f"target{i}_{j}")
            t.w32(children + j * 4, child)
            t.w32(child, t.vtable("target"))
            t.w32(child + 4, group)
            t.w32(child + 8, player)
            t.w32(child + 12, t.rng.choice([0, 0, 0, 1, 2, 3]))
    t.args(r3=player, r4=t.rng.choice([0, 1, 2, 0x80, 0xFF, 0x100, 0x80000101]))
