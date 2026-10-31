"""D660: active byte gates slot 7; normalize the returned byte to bool.

An inactive state may have a null creature pointer. An active one must have
a valid virtual receiver, as in the original. Observe all calls and memory.
"""
from liftcheck.spec import *

FUNCTION = "pongPlayer::IsCreatureStateReady"
ADDRESS = 0x820CD660
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000
RESULT = 0

CALLS = {"primary.vfn_7": stub(ret=lambda ctx: RESULT, args=("r3",))}


def inputs(t):
    global RESULT
    state = t.alloc(0x200, "state", fill="zero")
    primary = t.alloc(16, "primary")
    t.w32(primary, t.vtable("primary"))
    active = [0, 1, 2, 255][t.index % 4]
    RESULT = [0, 1, 2, 255][(t.index // 4) % 4]
    t.w8(state + 0x14, active)
    t.w32(state + 0x8C, primary if active or (t.index // 4) % 2 == 0 else 0)
    t.args(r3=state)
