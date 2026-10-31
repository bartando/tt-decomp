"""0x820CB368: movement-rate paths, exact FP and resolver side effects.

Unlike the input-speed helper, the latched path snapshots the rate before the
character resolver; the unlatched path reads it afterwards. The apparently
redundant (rate-rate)*fraction + rate must preserve signed zero and rounding.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover_GetMovementRate"
ADDRESS = 0x820CB368
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 800
FP_CONTRACT = "off"
EXTERNS = {"g_pInputArrayTable": 0x825EAB28, "g_gameDataMgr": 0x8271A2E4}


def resolve(ctx):
    character, manager = struct.unpack(">II", ctx.read(ctx.r(3), 8))
    ctx.write(0x8271A2E4, struct.pack(">I", manager))
    ctx.ret(r3=character)


CALLS = {0x821C9C00: model(resolve, args=("r3", "r4"))}


def inputs(t):
    rng = t.rng
    mover = t.alloc(0x110, "mover with guards") + 16
    match = t.alloc(0x200, "match slots")
    managers = [t.alloc(0x20, f"manager {i}") for i in range(2)]
    for i, manager in enumerate(managers):
        data = t.alloc(0x80, f"movement data {i}")
        t.floats(data + 0x58, 4, -50, 50)
        t.wf32(data + 0x5C, rng.choice((0., -0., -1., 5., float("inf"), -float("inf"), float("nan"), rng.uniform(-50, 50))))
        t.w32(manager + 0x14, data)
    character = t.alloc(0x40, "character")
    movement = t.alloc(0x80, "character movement")
    t.w32(character + 0x28, movement)
    t.wf32(movement + 0x6C, rng.choice((0., -0., -1., 0.5, rng.uniform(-10, 10))))
    t.w32(match, character)
    t.w32(match + 4, managers[1])
    index = rng.randrange(8)
    t.w32(mover + 0x44, index)
    t.w8(mover + 0x84, 0 if t.index % 4 < 2 else rng.choice((1, 128, 255)))
    t.w8(match + 36 * index + 0xC4, 0 if t.index % 2 else rng.choice((1, 128, 255)))
    t.wf32(mover + 0x78, rng.choice((-0., 0., -5., 1.75, 3., 1e30, float('nan'))))
    t.w32(t.sym("g_pInputArrayTable"), match)
    t.w32(t.sym("g_gameDataMgr"), managers[0])
    t.args(r3=mover)
