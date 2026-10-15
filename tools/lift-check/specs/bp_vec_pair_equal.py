"""ballPredict::VecPairEqual (0x821D4F80): two masked vector compares."""
import os, struct, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "ballPredict::VecPairEqual"
ADDRESS = 0x821D4F80
SOURCE = "src/game/ball/ball_predict.cpp"
EXTERNS = {"g_vectorComparisonMask": 0x82619BE0}


def inputs(t):
    rng = t.rng
    for k in range(4):
        t.w32(0x82619BE0 + 4 * k, rng.choice([0xFFFFFFFF, 0xFFFFFFFF, 0]))
    data = bytearray()
    for _ in range(8):
        data += struct.pack(">f", rng.choice([0.0, -0.0, 1.0, 1e-40, -3e-39, float("nan"), rng.uniform(-2.0, 2.0)]))
    other = bytearray(data)
    if rng.random() < 0.7:
        other[rng.randrange(32)] ^= 1 << rng.randrange(8)
    t.args(r3=t.alloc(32, "a", fill=bytes(data)), r4=t.alloc(32, "b", fill=bytes(other)))
