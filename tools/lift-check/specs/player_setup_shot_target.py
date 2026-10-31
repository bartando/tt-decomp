"""0x821A5DF8: mutable x/z clamp, opponent activity, movement parameters, return."""
import struct
from liftcheck.spec import *

FUNCTION = "pongPlayer_SetupShotTarget"
ADDRESS = 0x821A5DF8
SOURCE = "src/game/player/player_shot_target_setup.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def edge(rng):
    return rng.choice([-10.0, -1.0, -0.0, 0.0, 1.0, 10.0,
                       float("nan"), float("inf"), -float("inf"), rng.uniform(-20, 20)])


def bounds(ctx):
    for reg in (5, 6):
        ctx.write(ctx.r(reg), struct.pack(">4f", *(edge(ctx.rng) for _ in range(4))))


CALLS = {
    0x821C9CD0: model(bounds, args=("r3", "r4", "r5", "r6")),
    0x820CD598: run(),
    0x8218C7A8: stub(ret=lambda ctx: edge(ctx.rng)),
    0x82195DF0: stub(ret="void", args=("r3", "f1", "f2", "f3", "f4")),
}


def inputs(t):
    rng = t.rng
    target = t.alloc(0x4A0, "shotTarget", floats=[(0x480, 4), 0x494])
    owner = t.alloc(0x19F0, "player")
    opponent = t.alloc(0x200, "opponent")
    state = t.alloc(0xA0, "opponent.state")
    bound = t.alloc(0x60, "opponent.bound", floats=[0x50, 0x54])
    t.w32(target + 0x30, owner)
    slot = rng.randrange(4)
    t.w32(owner + 0x1D0, slot)
    t.w8(owner + 0x19E0, rng.choice([0, 0, 1, 2, 0xFF]))
    t.w32(owner + 0x1C4, opponent)
    t.w32(opponent + 0xBC, state)
    t.w32(opponent + 0xA8, bound)
    timing = t.alloc(0x34, "opponent.timing")
    t.wf32(timing + 0x1C, edge(rng))
    t.wf32(timing + 0x30, edge(rng))
    t.w32(state + 0x7C, rng.choice([0, timing, timing]))
    recovery = t.alloc(0xB0, "opponent.recovery")
    t.w8(recovery + 0x2C, rng.choice([0, 0, 1, 2]))
    t.wf32(recovery + 0xAC, edge(rng))
    t.w32(state + 0x80, rng.choice([0, recovery, recovery]))
    settings = t.alloc(0x60, "settings")
    for i in range(4):
        transform = t.alloc(0x40, f"root{i}")
        t.floats(transform + 0x30, 4, -20, 20)
        t.w32(settings + (17 + i) * 4, transform)
    t.w32(0x825EAB28, settings)
    position = t.alloc(16, "position", floats=[(0, 4)])
    if t.index % 6 == 0:
        position = target + 0x480
    for i in range(4):
        t.wf32(position + i * 4, edge(rng))
    t.args(r3=target, r4=position, f1=edge(rng), f2=edge(rng))
