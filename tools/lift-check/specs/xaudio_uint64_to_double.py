"""SDK unsigned conversion truncates, including the top 11 discarded bits.
Exercise every exponent and values around powers of two and halfway rounding
boundaries, plus arbitrary uint64 words. Exact binary64 return comparison.
"""
from liftcheck.spec import *
FUNCTION = "XAudio_UInt64ToDouble"
ADDRESS = 0x825693C0
SOURCE = "src/platform/audio_frame.cpp"
TRIALS = 1200

def inputs(t):
    rng = t.rng
    bit = t.index % 64
    value = rng.choice([0, 1, (1 << 64) - 1, rng.getrandbits(64),
                        (1 << bit) + rng.choice([-1, 0, 1]),
                        (1 << 63) + rng.randrange(1, 2048)])
    t.args(r3=value)
