"""0x820CE090: full matrix sample, pointer state and four translation lanes.

Index % 16 == 0 deliberately fails ID conversion. The original then uses an
uninitialized sampled row; ignore only output+0x30..+0x3F on those trials.
The three basis rows, helper calls and all other bytes remain checked.
"""
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


def matrix(ctx):
    ctx.write(ctx.r(4), struct.pack(">16f", *(ctx.rng.uniform(-5, 5) for _ in range(16))))


CALLS = {
    0x821C9C00: stub(ret=character, args=("r3", "r4")),
    0x821D0A30: run(args=("r3", "r4", "r5")),
    0x821D04F0: run(),
    0x8240E6D0: stub(ret="void", args=("r3",)),
    0x821D0880: model(matrix, args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    blender = t.alloc(0x20, "blender")
    slot = rng.randrange(4)
    t.w32(blender + 8, slot)
    sampleState = t.alloc(0x18, "sampleState")
    boneMap = t.alloc(0x20, "boneMap")
    failed_lookup = t.index % 16 == 0
    t.w32(boneMap + 0x14, 2 if failed_lookup else 0)
    t.w16(boneMap + 0x1C, 0)
    matrices = t.alloc(8 * 64, "sampleMatrices")
    t.floats(matrices, 8 * 16, -5, 5)
    t.w32(sampleState + 4, boneMap)
    t.w32(sampleState + 0x14, matrices)
    t.w32(blender + 0x1C, sampleState)
    settings = t.alloc(16, "settings")
    for i in range(4):
        char = t.alloc(0x30, f"character{i}")
        owner = t.alloc(0x14C, f"owner{i}")
        skeleton = t.alloc(0x44, f"skeleton{i}")
        t.w16(skeleton + 0x40, rng.randrange(8))
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
    if failed_lookup:
        t.ignore(output + 0x30, 16)
    t.args(r3=blender, r4=output)
