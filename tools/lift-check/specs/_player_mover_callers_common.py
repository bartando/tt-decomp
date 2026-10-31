from liftcheck.spec import *


def player(t):
    obj = t.alloc(0x2000, "player")
    creature = t.alloc(0xD0, "creature")
    mover = t.alloc(0x100, "mover")
    action = t.alloc(0x800, "action")
    settings = t.alloc(0x200, "settings")
    t.w32(0x825EAB28, settings)
    t.w32(obj + 0x1C4, creature)
    t.w32(creature + 0xA8, mover)
    t.w32(obj + 0x1F0, action)
    slot = t.index % 2
    t.w32(obj + 0x1D0, slot)
    t.w8(settings + 64 + slot, t.rng.choice([0, 1, 0x80, 0xFF]))
    t.w32(settings + (slot + 14) * 4, t.rng.choice([0, 0, 1, -1]))
    return obj
