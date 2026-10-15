"""pongCreature_StartServeBlender (0x820C7248).

r3 the creature, r4/r5 two 12-byte callbacks copied into the serve blender
(+0x50/+0x60). The original inlines 0x820CD550 twice; CancelSwing and
pongServeBlender_Start are stubs (their args compared). 0x820CAB48 writes the
position to r3 and returns it; the original passes that return value on.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403,E402
from player_common import fill_vec_return_dest, inlined, match_settings, timing_state  # noqa: E402

FUNCTION = "pongCreature_StartServeBlender"
ADDRESS = 0x820C7248
SOURCE = "src/game/player/pong_player.cpp"

CALLS = {
    0x820CD550: inlined(),
    0x820CD908: stub(ret="void"),                 # CancelSwing(blender)
    0x820CAB48: model(fill_vec_return_dest),
    0x820DD060: stub(ret=0),                      # pongServeBlender_Start
}


def inputs(t):
    rng = t.rng
    match_settings(t)
    creature = t.alloc(0xD0, "creature", fill="zero")
    t.w32(creature + 0xA8, t.alloc(0x40, "bound"))
    t.w32(creature + 0xCC, rng.randrange(0, 2))
    blender = t.alloc(0x100, "blender", fill="zero")
    t.w32(creature + 0xBC, blender)
    if rng.random() < 0.85:
        t.w32(blender + 0x7C, timing_state(t))
    swing = t.alloc(0xB0, "swingAnim")
    t.w32(blender + 0x80, swing)
    sub94 = t.alloc(0x30, "sub94", fill="zero")
    t.w32(sub94 + 0x1C, rng.choice([0, 0, 1]))
    t.w32(sub94 + 0x20, rng.choice([0, 1, 2]))
    t.w32(sub94 + 0x24, rng.choice([3, 3, 2]))
    t.w32(blender + 0x94, sub94)
    action = t.alloc(0x0C, "action")
    query = t.alloc(0x0C, "query")
    t.args(r3=creature, r4=action, r5=query)
