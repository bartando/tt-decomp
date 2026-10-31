"""Weighted sampling, latched flags, double clamps and exact MWC state."""
from liftcheck.spec import *
FUNCTION = "pongPlayer_66A8_g"
ADDRESS = 0x821A66A8
SOURCE = "src/game/player/ai_swing_direction.cpp"
TRIALS = 1000
FP_CONTRACT = "off"

def inputs(t):
    direction = t.alloc(0x60, "direction")
    values = [-float("inf"), -100., -1., -0., 0., 1., 2., 100., float("inf"), float("nan")]
    t.w8(direction + 0x58, t.rng.choice([0, 0, 0, 1, 2, 255]))
    for i in range(4):
        t.w8(direction + 0x54 + i, 0 if t.index % 3 else t.rng.choice([0, 1, 2, 255]))
        for p in [direction + 0x34 + i * 8, direction + 0x38 + i * 8]:
            t.wf32(p, t.rng.choice(values) if t.index < 300 else t.rng.uniform(-100, 100))
    for offset in [0x1c, 0x20, 0x2c, 0x30]:
        t.wf32(direction + offset, t.rng.choice(values) if t.index < 300 else t.rng.uniform(-5, 100))
    t.w32(0x825ca2c8, t.rng.getrandbits(32))
    t.w32(0x825ca2cc, t.rng.getrandbits(32))
    t.args(r3=direction)
