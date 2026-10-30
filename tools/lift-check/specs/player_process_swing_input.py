"""0x820C73E8: both readiness gates, low-byte poll, full vector store and return.
Run default 1000 trials with --seed 1 and --seed 7.
"""
import struct
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _swing_common import *

FUNCTION = "pongPlayer_73E8_g"
ADDRESS = 0x820C73E8
SOURCE = "src/game/player/pong_player_swing.cpp"
TRIALS = 1000


def ready(ctx):
    return ctx.rng.choice([0, 1])


def poll(ctx):
    return ctx.rng.choice([0, 1, 2, 255, 256, 257])


def compute(ctx):
    value = ctx.rng.choice([0.0, -0.0, 0.1, -1.0, float("nan"), ctx.rng.uniform(-3, 3)])
    ctx.write(ctx.r(5), struct.pack(">f", value))
    ctx.write(ctx.r(6), b"".join(struct.pack(">f", ctx.rng.uniform(-10, 10)) for _ in range(4)))


CALLS = {
    0x820CC3C8: stub(ret=ready),
    0x821C9D68: stub(ret=poll),
    0x820D42E0: model(compute, args=("r3", "r4", "r5", "r6", "f1")),
    0x820DC7A0: stub(ret=lambda c: c.rng.getrandbits(32)),
}


def inputs(t):
    settings(t)
    player = t.alloc(0x200, "player")
    state = t.alloc(0x200, "state")
    t.w32(player + 0xBC, state)
    t.w32(state + 0x94, swing(t))
    anim = t.alloc(0x1B0, "animation", floats=[0x19C])
    t.w32(state + 0x88, anim)
    bound = t.alloc(0x80, "bound")
    owner = t.alloc(0x200, "bound.owner")
    other = t.alloc(0x200, "otherState")
    t.w32(player + 0xA8, bound)
    t.w32(bound + 0x70, owner)
    t.w32(owner + 0xBC, other)
    t.w32(other + 0x94, t.pick([0, swing(t)]))
    t.args(r3=player, f1=edge_float(t))
