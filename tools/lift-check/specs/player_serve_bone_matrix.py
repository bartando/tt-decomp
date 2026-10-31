"""0x820CE090: resolve both bone samples and advance all translation lanes."""
import struct
from liftcheck.spec import *

FUNCTION = "game_E090"
ADDRESS = 0x820CE090
SOURCE = "src/game/player/player_serve_hit_point.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def character(ctx):
    settings = ctx.r(3)
    slot = ctx.r(4)
    return int.from_bytes(ctx.read(settings + 4 * slot, 4), "big")


def motion(ctx):
    ctx.write(ctx.r(4), struct.pack(">4f", *(ctx.rng.uniform(-5, 5) for _ in range(4))))


def matrix(ctx):
    ctx.write(ctx.r(4), struct.pack(">16f", *(ctx.rng.uniform(-5, 5) for _ in range(16))))


CALLS = {
    0x821C9C00: stub(ret=character, args=("r3", "r4")),
    0x821D0A30: model(motion, args=("r3", "r4", "r5")),
    0x821D0880: model(matrix, args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    blender = t.alloc(0x20, "blender")
    slot = rng.randrange(4)
    t.w32(blender + 8, slot)
    t.w32(blender + 0x1C, rng.getrandbits(32))
    settings = t.alloc(16, "settings")
    for i in range(4):
        char = t.alloc(0x30, f"character{i}")
        owner = t.alloc(0x14C, f"owner{i}")
        skeleton = t.alloc(0x30, f"skeleton{i}")
        t.w32(char + 0x2C, owner)
        t.w32(owner + 0x148, skeleton)
        t.w32(settings + i * 4, char)
    t.w32(0x825EAB28, settings)
    ballSlot = t.alloc(4, "ballSlot")
    instance = t.alloc(8, "instance")
    body = t.alloc(0x10, "body")
    timing = t.alloc(0x0C, "timing")
    t.w32(ballSlot, rng.choice([0, instance]))
    t.w32(instance + 4, body)
    t.w32(body + 0x0C, timing)
    t.wf32(timing + 8, rng.choice([-1.0, -0.0, 0.0, 1.0, rng.uniform(-3, 3)]))
    t.w32(0x8271A2F4, ballSlot)
    node = t.alloc(0x90, "ballNode")
    t.wf32(node + 0x8C, rng.choice([-1.0, -0.0, 0.0, 0.1, 1.0, 2.0, float("inf"), float("nan")]))
    t.w32(0x82606570, node)
    output = t.alloc(64, "matrix", floats=[(0, 16)])
    t.args(r3=blender, r4=output)
