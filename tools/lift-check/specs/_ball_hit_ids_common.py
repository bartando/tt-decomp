"""Shared hit-ID fixtures: ring wrap, live metadata changes and query scripts."""
import struct
from liftcheck.spec import *


def u32(ctx, a):
    return struct.unpack(">I", ctx.read(a, 4))[0]


def put32(ctx, a, n):
    ctx.write(a, struct.pack(">I", n & 0xFFFFFFFF))


def script(ctx):
    return u32(ctx, u32(ctx, 0x825EAB28) + 0x48)


def mutate(ctx, data):
    control = script(ctx)
    if u32(ctx, control + 0x18):
        put32(ctx, data + 0x2608, u32(ctx, control + 0x1C))
    if u32(ctx, control + 0x20):
        put32(ctx, 0x8271A2F8, u32(ctx, control + 0x24))
    if u32(ctx, control + 0x28):
        put32(ctx, 0x8271A2E8, u32(ctx, control + 0x2C))
    if u32(ctx, control + 0x30):
        put32(ctx, data + 0x25A4, u32(ctx, control + 0x34))
        put32(ctx, data + 0x25A8, u32(ctx, control + 0x38))


def query(counter_offset, result_offset):
    def call(ctx):
        control = script(ctx)
        n = u32(ctx, control + counter_offset)
        put32(ctx, control + counter_offset, n + 1)
        mutate(ctx, ctx.r(3))
        ctx.ret(r3=u32(ctx, control + result_offset + 4 * min(n, 3)))
    return call


def needs(ctx):
    mutate(ctx, ctx.r(3))
    ctx.ret(r3=u32(ctx, script(ctx) + 0x10))


def forecast(ctx):
    control = script(ctx)
    ctx.write(ctx.r(3), ctx.read(control + 0x90, 0x50))
    put32(ctx, ctx.r(4), u32(ctx, control + 0x14))
    mutate(ctx, u32(ctx, control + 0xE0))


CALLS = {
    "BallPredict_FindNetContact": model(query(0, 0x40), args=("r3", "r4")),
    "BallPredict_FindBounceOnSide": model(query(4, 0x50), args=("r3", "r4", "r5")),
    "BallPredict_FindDepartingSample": model(query(8, 0x60), args=("r3", "r4")),
    "BallPredict_FindReturnAcrossNet": model(query(12, 0x70), args=("r3", "r4")),
    "BallPredict_NeedsOutcomeForecast": model(needs, args=("r3", "r4")),
    "BallPredict_MarkHittableWindow": stub(ret="void", args=("r3", "r4", "r5", "r6", "r7")),
    "BallPredict_MarkLateTableExit": stub(ret="void", args=("r3", "r4", "r5"), deref={"r4": 12}),
    "BallPredict_ForecastOutcome": model(forecast, args=("r3", "r4", "r5"), deref={"r3": 0x50}),
    "gdBallPredictData::FindFirstHittable": run(),
    "gdBallPredictData::FindFirstUnhittableFrom": run(),
    "nop_8240E6D0": stub(ret="void", args=("r3",)),
}


def inputs(t, recovery=False):
    rng = t.rng
    # Forecast's sample padding is uninitialised in both originals and ignored
    # by real sample assignment. A zero stack makes forced snapshots comparable.
    original = rng.randbytes
    rng.randbytes = lambda n: bytes(n) if n == 0x9000 else original(n)
    control = t.alloc(0x100, "query script")
    input_obj = t.alloc(0x50, "input")
    t.w32(input_obj + 0x48, control)
    t.w8(input_obj + 0x40, rng.choice([0, 1, 2, 255]))
    t.w8(input_obj + 0x41, rng.choice([0, 1, 2, 255]))
    t.w32(0x825EAB28, input_obj)

    def clock(name):
        p = t.alloc(0x40, name)
        t.wf32(p + 0x30, rng.uniform(20, 40))
        return p

    clocks = [clock("initial clock"), clock("replacement clock")]
    t.w32(0x8271A2E8, clocks[0])
    data = t.alloc(0x2800, "prediction")
    tail = rng.choice([0, 1, 117, 118, 119])
    count = rng.choice([8, 12, 30, 119, 120])
    t.w32(data + 0x25A0, (tail + count) % 120)
    t.w32(data + 0x25A4, tail)
    t.w32(data + 0x25A8, count)
    ids = [t.alloc(16, "initial IDs"), t.alloc(16, "replacement IDs")]
    t.w32(data + 0x2608, ids[0])
    t.w16(data + 0x260C, 4)
    t.w16(data + 0x260E, 4)
    t.wf32(data + 0x2610, rng.uniform(-10, -1))

    mode = t.index % 8
    first = [-1, 0, 1, 3, 1, 3, 1, 4][mode]
    for i in range(120):
        sample = data + 0x20 + ((tail + i + 1) % 120) * 0x50
        t.wf32(sample, i * 0.125 + rng.uniform(0.001, 0.01))
        t.wf32(sample + 4, rng.uniform(2, 8))
        t.floats(sample + 0x10, 16, -5, 5)
        t.wf32(sample + 0x18, rng.choice([-0.0, 0.0, -2.0, 2.0, float("nan")]))
        eligible = first >= 0 and i >= first
        if mode in (3, 5):
            eligible = eligible and i < first + 2
        t.w8(sample + 8, (1 if mode == 3 else 0) if i == first + 2 else 0)
        t.w8(sample + 9, rng.choice([0, 1, 255]))
        t.w8(sample + 10, rng.choice([1, 17, 255]) if eligible else 0)
    states = [t.alloc(0x20, "state"), t.alloc(0x20, "replacement state")]
    for state in states:
        t.w32(state + 0x14, data)
    t.w32(0x8271A2F8, states[0])
    slot = rng.choice([0, 1, 2, -1]) if recovery else rng.randrange(2)
    t.w32(0x82606578, slot)
    for player in range(2):
        t.w16(0x8261A3D0 + player * 0x1A0 + 0xF6, rng.choice([0, 0x1000, 0x1001]))
    for off in range(0, 16, 4):
        t.w32(control + off, 0)
    t.w32(control + 0x10, rng.choice([0, 0x100, 1, 255, 0x101]))
    t.w32(control + 0x14, rng.choice([0, 1, 2, 3, 4, 0xFFFFFFFF]))
    t.w32(control + 0x18, rng.choice([0, 1]))
    t.w32(control + 0x1C, ids[1])
    t.w32(control + 0x20, rng.choice([0, 1]))
    t.w32(control + 0x24, states[1])
    t.w32(control + 0x28, rng.choice([0, 1]))
    t.w32(control + 0x2C, clocks[1])
    t.w32(control + 0x30, rng.choice([0, 1]))
    t.w32(control + 0x34, rng.choice([0, 117, 119]))
    t.w32(control + 0x38, rng.choice([8, 30, 119, 120]))
    for off in range(0x40, 0x80, 4):
        t.w32(control + off, rng.choice([-4, -3, -2, -1, 0, 1, 3, 6, 7]))
    for off in range(0x90, 0xE0, 4):
        t.wf32(control + off, rng.uniform(-3, 3))
    t.wf32(control + 0x90, rng.uniform(50, 60))
    t.wf32(control + 0xA0, rng.choice([0.0, -1.36, 1.36, 1.359, 1.361, 2.0]))
    t.wf32(control + 0xA8, rng.choice([0.0, -1.71, 1.71, 1.709, 1.711, 2.0]))
    t.w32(control + 0xE0, data)
    t.wf32(0x825C7554, 1.36)
    t.wf32(0x825C7558, 1.71)
    t.args(r3=rng.getrandbits(32))
