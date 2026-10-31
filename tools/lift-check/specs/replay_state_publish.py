"""Replay request flags, empty/null lists, lockout, and pointer publication."""
from liftcheck.spec import *
FUNCTION = "util_CE00"
ADDRESS = 0x821CCE00
SOURCE = "src/game/match/replay_state_publish.cpp"
TRIALS = 128

def inputs(t):
    replay = t.alloc(0x68D20, "replay", fill="zero")
    context = t.alloc(64, "match context")
    entry_list = t.alloc(16, "entry list") if t.index % 4 else 0
    target = t.alloc(16, "replay target") if t.index % 3 else 0
    t.w32(0x8271A2FC, context)
    for off in (0x68CFB, 0x68CFC, 0x68CFD):
        t.w8(replay + off, t.rng.choice([0, 0, 0, 1, 2, 255]))
    t.w8(replay + 0x68CFE, t.rng.choice([0, 0, 0, 1, 255]))
    t.w8(context + 0x24, t.rng.choice([0, 0, 0, 1, 255]))
    t.w32(replay + 0x68D10, entry_list)
    t.w32(replay + 0x68D00, target)
    if entry_list:
        t.w16(entry_list + 4, t.rng.choice([0, 0, 1, 2, 65535]))
    t.args(r3=replay)
