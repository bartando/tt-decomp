"""0x82282508: spin octant selects character trail strengths; diagonal lookups
can return distinct characters and replace the first character's parameter data."""
import struct
from liftcheck.spec import *

FUNCTION = "game_2508"
ADDRESS = 0x82282508
SOURCE = "src/game/ball/ball_shot.cpp"
TRIALS = 1200
EXTERNS = {"g_currentInputSlot": 0x82606578}


def _u32(ctx, addr):
    return struct.unpack(">I", ctx.read(addr, 4))[0]


def _character(ctx):
    script = ctx.r(3)
    count, first, second, replacement, new_match, new_slot = struct.unpack(">6I", ctx.read(script, 24))
    ctx.write(script, struct.pack(">I", count + 1))
    ctx.write(0x825EAB28, struct.pack(">I", new_match))
    ctx.write(0x82606578, struct.pack(">I", new_slot))
    if count:
        ctx.write(first + 0x28, struct.pack(">I", replacement))
    ctx.ret(r3=first if count == 0 else second)


CALLS = {
    "pongBall_ClassifySpin": stub(ret=lambda ctx: _u32(ctx, ctx.r(3) + 12)),
    "pongMatch_GetCharacterForSlot": model(_character),
}


def inputs(t):
    rng = t.rng
    spin = t.alloc(16, "spin", floats=[(0, 3)])
    velocity = t.alloc(16, "velocity", floats=[(0, 4)])
    t.floats(spin, 3, -100, 100)
    t.floats(velocity, 4, -100, 100)
    # Invalid classifications exercise the unsigned bounds check too.
    direction = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 0xffffffff, 0x80000000][t.index % 12]
    t.w32(spin + 12, direction)
    chars = [t.alloc(0x30, f"character {i}") for i in range(2)]
    params = [t.alloc(0x20, f"trail parameters {i}", floats=[(0x10, 4)]) for i in range(3)]
    for p in params:
        t.floats(p + 0x10, 4, -100, 100)
    for c, p in zip(chars, params):
        t.w32(c + 0x28, p)
    script = t.alloc(24, "match lookup script")
    for off, val in enumerate([0, *chars, params[2], t.alloc(24, "new match"), rng.getrandbits(32)]):
        t.w32(script + off * 4, val)
    t.w32(0x825EAB28, script)
    t.w32(0x82606578, rng.getrandbits(32))
    t.args(r3=spin, r4=velocity)
