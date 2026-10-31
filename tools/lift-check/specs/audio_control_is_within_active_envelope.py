"""0x8216EA00: active byte and the ordered (first sum, final sum] interval."""
import struct
from liftcheck.spec import *

FUNCTION = "AudioControl_IsWithinActiveEnvelope"
ADDRESS = 0x8216EA00
SOURCE = "src/game/ball/ball_audio_envelope.cpp"
TRIALS = 1000
EXTERNS = {"rage::phBoundCapsule::SumFloatArray": 0x82172C08}
CALLS = {0x82172C08: run(args=("r3", "r4"), deref={"r3": 0x44})}


def rounded(value):
    return struct.unpack(">f", struct.pack(">f", value))[0]


def inputs(t):
    rng = t.rng
    obj = t.alloc(0x80, "audio control")
    t.w8(obj + 0x24, rng.choice([0, 1, 2, 0x80, 255]))
    values = [rounded(rng.uniform(-5, 5)) for _ in range(5)]
    if t.index % 11 == 0:
        values[t.index % 5] = float("nan")
    if t.index % 13 == 0:
        values = [0.0, 0.0, 0.0, 0.0, 0.0]
    total = 0.0
    for i, value in enumerate(values):
        t.wf32(obj + 0x5C + 4 * i, value)
        total = rounded(total + value)
    threshold = rng.choice([values[0], total, rounded(values[0] + 0.01),
                            rounded(total + 0.01), rng.uniform(-10, 10),
                            float("nan"), float("inf"), float("-inf")])
    t.wf32(obj + 0x20, threshold)
    t.args(r3=obj)
