"""Player-manager gate, logged character-zero fallback, and live manager lookup.

The index resolver is scripted at its boundary, including replacing the data
manager. Its result and the incoming unused receiver are independently varied.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongMatch_GetCharacterForSlot"
ADDRESS = 0x821C9C00
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1200
# Canonical manager slot and game-data manager loaded by the instructions.
EXTERNS = {"g_plrPlayerMgr_state": 0x82606430, "g_gameDataMgr": 0x8271A2E4}


def resolve(ctx):
    script = struct.unpack(">I", ctx.read(0x82606430, 4))[0]
    index, manager = struct.unpack(">II", ctx.read(script, 8))
    ctx.write(0x8271A2E4, struct.pack(">I", manager))
    ctx.ret(r3=index)


CALLS = {
    "pongMatch_GetCharacterIndex": model(resolve, args=("r3",)),
    "nop_8240E6D0": stub(ret="void", args=("r3",)),
}


def inputs(t):
    rng = t.rng
    script = t.alloc(16, "resolver script")
    managers = [t.alloc(32, f"data manager {i}") for i in range(2)]
    for i, manager in enumerate(managers):
        table = t.alloc(64, f"character array {i}")
        t.w32(manager + 24, table)
        for n in range(16):
            character = t.alloc(64, f"character {i}:{n}")
            t.w32(table + 4 * n, rng.choice([character, character, 0]))
    # Upper bits fall off the PPC's 32-bit scaled index, without signed UB.
    t.w32(script, rng.randrange(16) | rng.choice([0, 0x40000000, 0xc0000000]))
    t.w32(script + 4, managers[1])
    t.w32(0x82606430, rng.choice([0, script, script]))
    t.w32(0x8271A2E4, managers[0])
    t.args(r3=rng.getrandbits(32), r4=rng.getrandbits(32))
