"""0x820CB4D0: override, match-slot flag, and scaled character movement speed.

The character resolver can replace the live game-data manager. All call arguments,
returns, memory and guard bytes compare exactly. No ignored ranges.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover_GetInputSpeed"
ADDRESS = 0x820CB4D0
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 600
EXTERNS = {"g_pInputArrayTable": 0x825EAB28, "g_gameDataMgr": 0x8271A2E4}


def resolve(ctx):
    match = ctx.r(3)
    character, manager = struct.unpack(">II", ctx.read(match, 8))
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
        t.w32(manager + 0x14, data)
    character = t.alloc(0x40, "character")
    movement = t.alloc(0x80, "character movement")
    t.w32(character + 0x28, movement)
    t.wf32(movement + 0x64, rng.choice((0., -1., 0.5, rng.uniform(-10, 10))))
    t.w32(match, character)
    t.w32(match + 4, managers[1])
    index = rng.randrange(8)
    flags = rng.randrange(256)
    # Guarantee every route, including noncanonical true flag bytes.
    flags = (flags | 4) if t.index % 3 == 0 else (flags & ~4)
    t.w8(mover + 0x40, flags)
    t.w32(mover + 0x44, index)
    t.w8(match + 36 * index + 0xC4, 0 if t.index % 3 == 2 else rng.choice((1, 128, 255)))
    t.w32(t.sym("g_pInputArrayTable"), match)
    t.w32(t.sym("g_gameDataMgr"), managers[0])
    t.args(r3=mover)
