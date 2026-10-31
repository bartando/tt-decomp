"""D6B8: present secondary, false slot 6, then true slot 7.

Slot 6 can replace the state's secondary pointer. The second query must use
the replacement; all calls and writes remain observable. Exercise nulls,
all truth combinations and noncanonical nonzero bytes, without ignored data.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongPlayer::IsCreatureState2Active"
ADDRESS = 0x820CD6B8
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1000
STATE = REPLACEMENT = FIRST = SECOND = 0
REPLACE = False


def first(ctx):
    if REPLACE:
        ctx.write(STATE + 0x90, struct.pack(">I", REPLACEMENT))
    ctx.ret(r3=FIRST)


CALLS = {
    "secondary.vfn_6": model(first, args=("r3",)),
    "secondary.vfn_7": stub(ret=lambda ctx: SECOND, args=("r3",)),
    "replacement.vfn_7": stub(ret=lambda ctx: SECOND, args=("r3",)),
}


def inputs(t):
    global STATE, REPLACEMENT, FIRST, SECOND, REPLACE
    STATE = t.alloc(0x200, "state", fill="zero")
    secondary = t.alloc(16, "secondary")
    REPLACEMENT = t.alloc(16, "replacement")
    t.w32(secondary, t.vtable("secondary"))
    t.w32(REPLACEMENT, t.vtable("replacement"))
    FIRST = [0, 1, 2, 255][t.index % 4]
    SECOND = [0, 1, 2, 255][(t.index // 4) % 4]
    REPLACE = bool((t.index // 16) % 2)
    t.w32(STATE + 0x90, secondary if t.index % 5 else 0)
    t.args(r3=STATE)
