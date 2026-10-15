"""ballPredict::ShotEqual (0x821D5290): field-by-field compare of two 0xB8-byte shots."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "ballPredict::ShotEqual"
ADDRESS = 0x821D5290
SOURCE = "src/game/ball/ball_predict.cpp"
EXTERNS = {"g_vectorComparisonMask": 0x82619BE0, "ballPredict::VecPairEqual": 0x821D4F80}
CALLS = {0x821D4F80: run()}


def inputs(t):
    rng = t.rng
    # The mask is set by a static initializer (zero in the image).
    for k in range(4):
        t.w32(0x82619BE0 + 4 * k, rng.choice([0xFFFFFFFF, 0xFFFFFFFF, 0]))
    data = bytearray()
    for _ in range(0xB0 // 4):
        data += struct.pack(">f", rng.choice([0.0, -0.0, 1.0, 1e-40, rng.uniform(-2.0, 2.0)]))
    for off in (0x20, 0x88, 0x8C):
        data[off:off + 4] = struct.pack(">I", rng.randrange(4))
    data += bytes(rng.getrandbits(8) for _ in range(8))
    other = bytearray(data)
    # Change one byte (or none) so every early-out gets exercised.
    if rng.random() < 0.85:
        off = rng.randrange(0xB4, 0xB8) if rng.random() < 0.3 else rng.randrange(0xB8)
        other[off] ^= 1 << rng.randrange(8)
    a = t.alloc(0xB8, "a", fill=bytes(data))
    b = t.alloc(0xB8, "b", fill=bytes(other))
    t.args(r3=a, r4=b)
