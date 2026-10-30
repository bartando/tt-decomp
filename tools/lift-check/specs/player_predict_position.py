"""0x820CAB48: swing-present and extrapolation paths, bounds and pointer return.
Run default 1000 trials with --seed 1 and --seed 7.
"""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _swing_common import *

FUNCTION = "pongPlayer_AB48_g"
ADDRESS = 0x820CAB48
SOURCE = "src/game/player/pong_player_swing.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def delta(ctx):
    ctx.write(ctx.r(3), b"".join(struct.pack(">f", ctx.rng.choice([1e-40, -1e-40, 0.0, ctx.rng.uniform(-5, 5)])) for _ in range(4)))


CALLS = {0x821C9CD0: run(),
         0x820CAF18: model(delta, deref={"r5": 12, "r6": 12, "r7": 16})}


def inputs(t):
    settings(t)
    owner = creature(t, "owner")
    state = t.alloc(0x200, "state")
    t.w32(owner + 0xBC, state)
    t.w32(state + 0x94, t.pick([0, swing(t)]))
    bound = t.alloc(0x100, "bound")
    t.w32(bound + 0x70, owner)
    t.w32(bound + 0x44, t.pick(range(8)))
    t.wf32(bound + 0x30, edge_float(t))
    t.wf32(bound + 0x34, edge_float(t))
    out = t.alloc(16, "position", floats=[(0, 4)])
    t.args(r3=out, r4=bound)
