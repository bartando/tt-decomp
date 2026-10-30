"""Quantized float channel sample: index clamping, u16 sample, fused scale/bias.

Covers indices below, inside and past the table (including count 1) and finite
scales/biases. A zero sample count clamps to index -1 in both versions (reading
before the table); that case is left out.
"""
from liftcheck.spec import *

FUNCTION = "rage::DecodeQuantizedFloat"
ADDRESS = 0x82244CB8
SOURCE = "src/rage/animation/rage_anim.cpp"
FP_CONTRACT = "off"  # the original fuses explicitly (fmadds); nothing else may be


def inputs(t):
    rng = t.rng
    channel = t.alloc(24, "channel")
    count = rng.choice([1, 2, 3, rng.randint(1, 64)])
    samples = t.alloc(count * 2, "samples")
    for i in range(count):
        t.w16(samples + 2 * i, rng.choice([0, 1, 0x7FFF, 0x8000, 0xFFFF, rng.randrange(65536)]))
    t.w32(channel + 8, samples)
    t.w16(channel + 12, count)
    t.wf32(channel + 16, rng.choice([0.0, -0.0, 1.0, rng.uniform(-1000, 1000)]))
    t.wf32(channel + 20, rng.choice([0.0, rng.uniform(-1000, 1000)]))
    index = rng.choice([-0x80000000, -1, 0, count - 1, count, 0x7FFFFFFF, rng.randint(-5, count + 5)])
    t.args(r3=channel, r4=index & 0xFFFFFFFF)
