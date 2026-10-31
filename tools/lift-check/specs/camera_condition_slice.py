"""All-of conditions: ring wrapping, integer kinds, float equality and NaNs."""
from liftcheck.spec import *
FUNCTION = "pongCameraMgr_5CE8"
ADDRESS = 0x82215CE8
SOURCE = "src/game/camera/pong_camera_helpers.cpp"
TRIALS = 512

def inputs(t):
    record = t.alloc(20, "transition")
    replay = t.alloc(0x68D20, "replay", fill="zero")
    ring = t.alloc(24, "condition ring")
    events = t.alloc(8 * 8, "events")
    required = t.alloc(4 * 8, "required")
    t.w32(0x8271A2EC, replay)
    t.w32(replay + 0x68D1C, ring)
    t.w32(ring + 8, events)
    t.w32(ring + 0x10, 8)
    start = t.rng.randrange(16)
    count = t.rng.randrange(12)
    t.w32(record + 12, start)
    t.w32(record + 16, count)
    pairs = [(1, 42), (5, 0xFFFFFFFF), (6, 0), (6, 0x80000000),
             (6, 0x7FC00042), (0, 0), (7, 0), (0xFFFFFFFF, 0)]
    if t.index < len(pairs) * 2:
        kind, value = pairs[t.index // 2]
        t.w32(record + 12, 7)
        t.w32(record + 16, 1)
        t.w32(events + 7 * 8, kind)
        t.w32(events + 7 * 8 + 4, value)
        t.w32(required, kind)
        t.w32(required + 4, value ^ (0x80000000 if kind == 6 and t.index % 2 else 0))
        n = 1
    else:
        for i in range(8):
            kind, value = t.rng.choice(pairs)
            t.w32(events + i * 8, kind)
            t.w32(events + i * 8 + 4, value)
        for i in range(4):
            kind, value = t.rng.choice(pairs)
            t.w32(required + i * 8, kind)
            t.w32(required + i * 8 + 4, value)
        n = t.rng.choice([-3, 0, 1, 2, 4])
        if t.index % 11 == 0:
            required = 0
    t.args(r3=record, r4=required, r5=n)
