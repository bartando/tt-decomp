"""0x82195DF0: input gate, mover reloads, protected target and exact flag mask."""
import struct
from liftcheck.spec import *

FUNCTION = "io_5DF0"
ADDRESS = 0x82195DF0
SOURCE = "src/game/player/player_apply_movement_target.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def query(c):
    # The query can replace the creature chain: no mover may be cached before it.
    player = c.r(3)
    creature = c.read(player + 0x1C8, 4)
    c.write(player + 0x1C4, creature)
    c.ret(r3=c.rng.randrange(2))


CALLS = {0x82195B60: model(query, args=("r3",))}


def inputs(t):
    obj = t.alloc(0x2000, "player")
    settings = t.alloc(0x100, "settings")
    t.w32(0x825EAB28, settings)
    slot = t.index % 2
    t.w32(obj + 0x1D0, slot)
    t.w32(settings + (slot + 14) * 4, t.rng.choice([0, 1, -1]))
    for offset in (0x1C4, 0x1C8):
        creature = t.alloc(0xD0, "creature")
        bound = t.alloc(0x100, "mover", floats=[0x10, 0x14, 0x18, 0x1C, 0x48, 0x4C])
        t.w32(obj + offset, creature)
        t.w32(creature + 0xA8, bound)
        t.w8(bound + 0x40, t.rng.randrange(256))
    values = [t.rng.choice([0.0, -0.0, 1.0, -1.0, float("inf"),
                            float("nan"), t.rng.uniform(-20, 20)]) for _ in range(4)]
    values = [struct.unpack(">f", struct.pack(">f", v))[0] for v in values]
    t.args(r3=obj, f1=values[0], f2=values[1], f3=values[2], f4=values[3])
