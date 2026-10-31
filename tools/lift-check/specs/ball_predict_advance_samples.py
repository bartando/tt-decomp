"""Playback ring refill, live-bank repeat, per-sample state reload, exhausted fallback."""
import struct
from liftcheck.spec import *

FUNCTION = "BallPredict_AdvanceSamples"
ADDRESS = 0x82287930
SOURCE = "src/game/ball/ball_prediction_stream.cpp"
TRIALS = 1000
EXTERNS = {"RTDynamicCast": 0x82430978}


def u32(c, p):
    return struct.unpack(">I", c.read(p, 4))[0]


def w32(c, p, v):
    c.write(p, struct.pack(">I", v & 0xffffffff))


def pop(c):
    data = c.r(3)
    popped, state = struct.unpack(">II", c.read(data + 0x25AC, 8))
    w32(c, 0x8271A2F8, state)
    c.ret(r3=popped)


def step(c):
    p = c.r(3)
    # Different values in all lanes catch partial sample copies and stale samples.
    for off in (0, 4, *range(0x10, 0x50, 4)):
        f = struct.unpack(">f", c.read(p + off, 4))[0]
        c.write(p + off, struct.pack(">f", f + 0.25 * (1 + off)))
    for off in (8, 9, 10):
        c.write(p + off, bytes([(c.read(p + off, 1)[0] + 1) & 0xff]))
    state = u32(c, 0x8271A2F8)
    script = u32(c, state)
    next_state, count = struct.unpack(">II", c.read(script, 8))
    w32(c, script + 4, count + 1)
    w32(c, 0x8271A2F8, next_state)


def add(c):
    data, p = c.r(3), c.r(4)
    count = u32(c, data + 0x25A8)
    head = (u32(c, data + 0x25A0) + 1) % 120
    out = data + 0x20 + head * 0x50
    for off, size in ((0, 11), (0x10, 0x40)):
        c.write(out + off, c.read(p + off, size))
    w32(c, data + 0x25A0, head)
    w32(c, data + 0x25A8, count + 1)
    # Change the global after AddSample: the original retains its cached state.
    w32(c, 0x8271A2F8, u32(c, data + 0x25B4))


CALLS = {
    "gdBallPredictData::PopElapsed": model(pop, args=("r3", "r4")),
    "BallPredict_StepSample": model(step, args=("r3", "r4")),
    "gdBallPredictData::AddSample": model(add, args=("r3",)),
    "gdBallPredictData::AppendRepeatOfLast": stub(ret="void"),
    "gdBallPredictData::ExtendBounceList": stub(ret="void", args=("r3", "r4")),
    "RTDynamicCast": stub(ret=lambda c: c.r(3), args=("r3", "r4", "r5", "r6", "r7")),
    "rage_debugLog": stub(ret="void", args=("r3",)),
    "pongBallInstance::ActivateBall": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    states = [t.alloc(0x20, f"state{i}") for i in range(3)]
    data = []
    mode = t.index % 12
    popped = rng.choice([-2, -1, 0]) if mode < 3 else rng.choice([1, 2, 3, 7])
    for i, state in enumerate(states):
        script = t.alloc(8, f"script{i}")
        t.w32(state, script)
        t.w32(script, states[(i + 1) % len(states)])
        t.w32(script + 4, 0)
        banks = []
        for bank in range(2):
            d = t.alloc(0x2800, f"predict{i}:{bank}", ctype="gdBallPredictData")
            banks.append(d)
            count = rng.choice([0, 1, 2, 8, 119, 120]) if mode < 3 else rng.choice([1, 2, 8, 119, 120])
            tail = rng.randrange(120)
            t.w32(d + 0x25A0, (tail + count) % 120)
            t.w32(d + 0x25A4, tail)
            t.w32(d + 0x25A8, count)
            for n in range(120):
                t.floats(d + 0x20 + n * 0x50, 2, -10, 10)
                t.floats(d + 0x30 + n * 0x50, 16, -10, 10)
            last = d + 0x20 + ((tail + count) % 120) * 0x50
            last_time = struct.unpack(">f", t.arena[last - 0x40000000:last - 0x40000000 + 4])[0]
            t.wf32(d + 0x2604, last_time if mode in (3, 4, 5) else rng.choice([-999., float("nan")]))
            t.w8(d + 0x2600, 0 if mode >= 8 else rng.choice([0, 1, 0x80]))
            t.w32(d + 0x25AC, popped)
            t.w32(d + 0x25B0, states[1])
            t.w32(d + 0x25B4, states[2])
            t.w32(state + 0x10 + bank * 4, d)
        data.append(banks)
    ball = t.alloc(0xD0, "ball")
    slot = t.alloc(4, "ball slot")
    t.w32(slot, ball)
    t.w32(0x8271A2F4, slot)
    t.w32(0x8271A2F8, states[0])
    t.args(r3=rng.choice([0, 1]), r4=rng.choice([0, 1]))
