"""0x820CB4D0: forced, unscaled and character-scaled gameplay speeds."""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover_GetInputSpeed"
ADDRESS = 0x820CB4D0
SOURCE = "src/game/creature/mover_input_speed.cpp"
TRIALS = 1000
EXTERNS = {"g_gameDataMgr": 0x8271A2E4, "g_input_obj_ptr": 0x825EAB28}


def character(ctx):
    result, manager = struct.unpack(">II", ctx.read(ctx.r(3), 8))
    ctx.write(0x8271A2E4, struct.pack(">I", manager))
    ctx.ret(r3=result)


CALLS = {"pongMatch_GetCharacterForSlot": model(character)}


def value(t):
    return t.rng.choice([0.0, -0.0, 1.0, -1.0, 1.0e-39, -1.0e-39,
                         float("nan"), float("inf"), -float("inf"),
                         t.rng.uniform(-10, 10)])


def inputs(t):
    mover = t.alloc(0xE8, "mover")
    settings = t.alloc(0x140, "settings")
    char = t.alloc(0x30, "character")
    tuning = t.alloc(0x70, "characterTuning")
    managers = [t.alloc(0x20, f"manager{i}") for i in range(2)]
    for i, manager in enumerate(managers):
        config = t.alloc(0x70, f"gameplayConfig{i}")
        t.w32(manager + 0x14, config)
        t.wf32(config + 0x58, value(t))
        t.wf32(config + 0x64, value(t))
    t.w32(t.sym("g_gameDataMgr"), managers[0])
    t.w32(t.sym("g_input_obj_ptr"), settings)
    t.w32(settings, char)
    t.w32(settings + 4, managers[1])
    t.w32(char + 0x28, tuning)
    t.wf32(tuning + 0x64, value(t))
    slot = t.index % 3
    t.w32(mover + 0x44, slot)
    t.w8(mover + 0x40, t.rng.choice([0, 2, 4, 0x10, 0xFB, 0xFF]))
    t.w8(settings + slot * 36 + 0xC4, t.rng.choice([0, 0, 1, 2, 0x80, 0xFF]))
    t.args(r3=mover)
