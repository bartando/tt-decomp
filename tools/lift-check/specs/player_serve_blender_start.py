"""pongServeBlender_Start (0x820DD060): starts the serve blender if idle.

r3 the blender, r4 the position (16-byte copy), r5 canStart, r6 useAltClips.
The match clock comes from *0x8271A2E8 (+0x30); 0x825C9A2C decides whether
0x821CE0F0 runs on *0x8271A2EC.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import coin  # noqa: E402

FUNCTION = "pongServeBlender_Start"
ADDRESS = 0x820DD060
SOURCE = "src/game/player/pong_player.cpp"
FTOL = 0

CALLS = {
    0x820DD388: stub(ret=coin),       # refuses to start?
    0x820DD3E8: stub(ret="void"),
    0x8225E6E0: stub(ret="void"),     # PostGameMessage(id, flags, 0, 0)
    0x821CE0F0: stub(ret="void"),
}


def clip_list(t, name):
    n = t.rng.randrange(1, 5)
    items = t.alloc(4 * n, name, align=4)
    return items, n


def blender(t):
    rng = t.rng
    b = t.alloc(0xC0, "blender", ctype="pongSwingAnimView")
    t.w32(b + 0x04, rng.randrange(0, 4))                  # field_04: shift count
    creature = t.alloc(0xD0, "creature")
    t.w32(creature + 0xCC, rng.randrange(0, 2))           # player index
    t.w32(b + 0x08, creature)
    for off, name in ((0x0C, "clips"), (0x14, "altClips")):
        items, n = clip_list(t, name)
        t.w32(b + off, items)
        t.w16(b + off + 4, n)
    t.w8(b + 0x2C, rng.random() < 0.2)                    # pending
    t.wf32(b + 0xAC, rng.choice([0.5, 1.0, 1.5, rng.uniform(0, 2)]))
    return b


def inputs(t):
    rng = t.rng
    clock = t.alloc(0x40, "clock")
    t.wf32(clock + 0x30, rng.uniform(0, 500))
    t.w32(0x8271A2E8, clock)
    t.w32(0x8271A2EC, t.alloc(0x10, "a2ec"))
    t.w32(0x825C9A2C, rng.choice([1, 0xFFFFFFFF, 0]))
    pos = t.alloc(0x10, "position")
    t.floats(pos, 4, -3, 3)
    t.args(r3=blender(t), r4=pos, r5=rng.choice([0, 1]), r6=rng.choice([0, 1]))
