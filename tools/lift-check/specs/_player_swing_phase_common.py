"""Valid selected clip graphs with edge-case timings and signed frame markers."""
from liftcheck.spec import *


def state(t):
    rng = t.rng
    obj = t.alloc(0x1B0, "phase", floats=[0x60, 0x64, 0x19C])
    records = t.alloc(4 * 8, "records")
    for i in range(8):
        record = t.alloc(0x40, f"record{i}")
        clip = t.alloc(0x20, f"clip{i}")
        t.wf32(clip + 0x0C, rng.choice([
            -1.0, -0.0, 0.0, 0.01, 0.1, 1.0, 10.0, float("nan"),
            float("inf"), -float("inf"), rng.uniform(0.01, 10)]))
        t.w32(record + 0x10, clip)
        t.w32(record + 0x38, rng.choice([
            0, 1, -1, 10, -10, 0x7FFFFFFF, 0x80000000, rng.getrandbits(32)]))
        t.w32(records + 4 * i, record)
    t.w32(obj + 4, records)
    t.w32(obj + 0x194, rng.randrange(8))
    t.w32(obj + 0x198, rng.choice([0, 1, 2, 7, 8, 31, 32, 63, 64, -1]))
    t.wf32(obj + 0x19C, rng.choice([
        -1.0, -0.0, 0.0, 0.1, float("nan"), float("inf"), -float("inf")]))
    t.w16(obj + 0x5A, rng.choice([0, 1, 2, 0xFFFE, 0xFFFF]))
    return obj
