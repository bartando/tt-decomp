"""0x820DD3E8: slot stride, start/end times, four-lane roots and motion call."""
import struct
from liftcheck.spec import *

FUNCTION = "game_D3E8"
ADDRESS = 0x820DD3E8
SOURCE = "src/game/player/player_serve_hit_point.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def motion(ctx):
    ctx.write(ctx.r(3), struct.pack(">4f", *(ctx.rng.uniform(-10, 10) for _ in range(4))))
    ctx.ret(r3=ctx.r(3))


CALLS = {0x820DBBF8: model(motion, args=("r3", "r4", "f1", "f2"))}


def inputs(t):
    rng = t.rng
    slot = rng.randrange(2)
    obj = t.alloc(0xB0, "blender")
    clip = t.alloc(0x30, "clip")
    clipData = t.alloc(0x10, "clipData")
    t.w32(clip + 0x10, rng.choice([0, 1, 2, -1]))
    t.w32(clip + 0x1C, rng.choice([0, 1, -1, 30, 0x7FFFFFFF, 0x80000000, rng.getrandbits(32)]))
    t.w32(clip + 0x24, clipData)
    t.wf32(clipData + 0x0C, rng.choice([-1.0, -0.0, 0.0, 0.1, 1.0, 10.0, float("nan"), float("inf")]))
    t.w32(obj + 4, slot)
    t.w32(obj + 0x24, clip)
    t.w32(obj + 0x28, rng.randrange(4))
    t.wf32(obj + 0x30, rng.uniform(-5, 10))
    hits = t.alloc(4 * 4, "hits")
    for i in range(4):
        hit = t.alloc(0x70, f"hit{i}")
        t.floats(hit + 0x60, 4, -10, 10)
        t.w32(hits + i * 4, hit)
    t.w32(clip + 0x2C, hits)
    settings = t.alloc(0x50, "settings")
    for i in range(2):
        transform = t.alloc(0x40, f"transform{i}")
        t.floats(transform + 0x30, 4, -10, 10)
        t.w32(settings + (17 + i) * 4, transform)
    t.w32(0x825EAB28, settings)
    clock = t.alloc(0x40, "clock")
    t.wf32(clock + 0x30, rng.uniform(-5, 10))
    t.w32(0x8271A2E8, clock)
    for i in range(2):
        t.floats(0x82619990 + i * 80 + 8, 1, -10, 10)
        t.floats(0x82619990 + i * 80 + 0x10, 4, -10, 10)
        t.floats(0x82619990 + i * 80 + 0x20, 1, -10, 10)
        t.floats(0x82619990 + i * 80 + 0x30, 4, -10, 10)
    t.args(r3=obj)
