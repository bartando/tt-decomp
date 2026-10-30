"""0x820D42E0: type dispatch, fsel edge cases, four-lane target and live court clamp.
Run default 1000 trials with --seed 1 and --seed 7.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _swing_common import *

FUNCTION = "pongPlayer_42E0_g"
ADDRESS = 0x820D42E0
SOURCE = "src/game/player/pong_player_swing.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def raw_strength(ctx):
    return struct.unpack(">f", struct.pack(">f", ctx.rng.choice([-2.0, -0.0, 0.0, 0.1, 1.0, float("nan"),
                           float("inf"), -float("inf"), ctx.rng.uniform(-4, 4)])))[0]


CALLS = {"strength.vfn_10": stub(ret=raw_strength), 0x821C9CD0: run()}


def inputs(t):
    settings(t)
    obj = swing(t)
    power = t.alloc(16, "strength")
    target = t.alloc(16, "target", floats=[(0, 4)])
    # Output may overlap the source vector; retain original load/store order.
    if t.index % 5 == 0:
        target = obj + 0x180
    t.args(r3=obj, r4=t.rng.getrandbits(32), r5=power, r6=target, f1=edge_float(t))
