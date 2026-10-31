"""Fixtures for marking windows, late exits and bounded sample extrapolation."""
import math
import struct
from liftcheck.spec import *


def u32(ctx, a):
    return struct.unpack(">I", ctx.read(a, 4))[0]


def put32(ctx, a, n):
    ctx.write(a, struct.pack(">I", n & 0xFFFFFFFF))


def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def world(t, finite_radius=False):
    rng = t.rng
    table = t.alloc(0x20, "table")
    height = f32(rng.choice([0.0, 0.76, 1.0]))
    t.wf32(table + 0x14, height)
    t.w32(0x8271A304, table)
    ball = t.alloc(0x10, "ball")
    archetype = t.alloc(0x10, "archetype")
    bound = t.alloc(0x10, "bound")
    radius = f32(0.02) if finite_radius else f32(rng.choice([0.0, 0.02, 0.5, float("nan")]))
    t.w32(ball + 4, archetype)
    t.w32(archetype + 0xC, bound)
    t.wf32(bound + 8, radius)
    slot = t.alloc(4, "ball slot")
    if not finite_radius and rng.random() < 0.25:
        radius = 0.0
        t.w32(slot, 0)
    else:
        t.w32(slot, ball)
    t.w32(0x8271A2F4, slot)
    t.wf32(0x825C7554, 1.36)
    t.wf32(0x825C7558, 1.71)
    return height, radius


def prediction(t):
    rng = t.rng
    data = t.alloc(0x2800, "prediction")
    state = t.alloc(0x20, "state")
    t.w32(state + 0x14, data)
    t.w32(0x8271A2F8, state)
    count = rng.choice([0, 1, 2, 3, 4, 5, 8, 30, 119, 120])
    tail = rng.choice([0, 1, 117, 118, 119])
    t.w32(data + 0x25A4, tail)
    t.w32(data + 0x25A8, count)
    return state, data, count, tail


def at(data, tail, i):
    return data + 0x20 + ((tail + i + 1) % 120) * 0x50


def window_inputs(t):
    rng = t.rng
    _, radius = world(t)
    state, data, count, tail = prediction(t)
    decoy_state = t.alloc(0x20, "decoy global state")
    decoy_data = t.alloc(0x2800, "decoy prediction")
    t.w32(decoy_state + 0x14, decoy_data)
    t.w32(0x8271A2F8, decoy_state)
    start = rng.choice([0, 1, max(0, count - 1), count, count + 2])
    for i in range(120):
        sample = at(data, tail, i)
        t.w8(sample + 8, rng.choice([0, 0, 0, 1, 255]))
        t.w8(sample + 10, rng.choice([0, 1, 7, 255]))
        t.wf32(sample + 0x14, rng.choice([radius, radius + 0.01, radius - 0.01, 2.0, float("nan")]))
    leading = rng.randrange(7)
    for i in range(leading):
        t.w8(at(data, tail, start + i) + 8, rng.choice([1, 255]))
    t.w8(at(data, tail, start + leading) + 8, 0)
    t.args(r3=state, r4=rng.getrandbits(32), r5=start, r6=count,
           r7=rng.choice([0, 1, 7, 255, rng.getrandbits(32)]))


def late_inputs(t):
    rng = t.rng
    fixture_case = t.index % 16
    force_valid = fixture_case < 8
    height, radius = world(t, finite_radius=force_valid)
    threshold = f32(height + radius)
    _, data, count, tail = prediction(t)
    if force_valid:
        count = 30
        t.w32(data + 0x25A8, count)
    original_ids = t.alloc(16, "prediction IDs")
    t.w32(data + 0x2608, original_ids)
    other_array = t.alloc(16, "caller ID array")
    other_ids = t.alloc(16, "caller IDs")
    t.w32(other_array, other_ids)
    array = rng.choice([data + 0x2608, other_array])
    start = rng.choice([0, 1, max(0, count - 1), count])
    low = start + rng.choice([0, 1, 2, 3, 4, 5])
    if force_valid:
        array = other_array
        start, low = 0, 2 if fixture_case == 1 else 3
        t.w32(original_ids, rng.getrandbits(32) & ~16)
        t.w32(other_ids, rng.getrandbits(32) & ~16)
    for i in range(120):
        sample = at(data, tail, i)
        t.wf32(sample + 0x14, threshold + 1.0)
        t.wf32(sample + 0x10, rng.choice([0.0, 1.36, -1.36, 1.359, -1.359, 2.0, float("nan")]))
        t.wf32(sample + 0x18, rng.choice([0.0, 1.71, -1.71, 1.709, -1.709, 2.0, float("nan")]))
        t.w8(sample + 8, rng.choice([0, 0, 1, 255]))
        t.w8(sample + 10, rng.choice([0, 1, 7, 255]))
    if low < count:
        t.wf32(at(data, tail, low) + 0x14, rng.choice([threshold, threshold - 0.01]))
        if force_valid:
            sample = at(data, tail, low)
            t.wf32(sample + 0x10, 0.0)
            t.wf32(sample + 0x18, 0.0)
            t.w8(sample + 8, 0)
            t.w8(sample + 10, 1)
            if fixture_case == 2:
                t.wf32(sample + 0x10, 1.36)
            elif fixture_case == 3:
                t.wf32(sample + 0x18, 1.71)
            elif fixture_case == 4:
                t.w8(sample + 10, 0)
            elif fixture_case == 5:
                t.w8(sample + 8, 1)
            elif fixture_case == 6:
                t.wf32(at(data, tail, 0) + 0x14, float("nan"))
            elif fixture_case == 7:
                t.wf32(sample + 0x14, height)
    if low + 1 < count and not (force_valid and fixture_case == 7):
        # The scan must classify its first low sample, rather than searching
        # onwards for a more convenient later candidate.
        sample = at(data, tail, low + 1)
        t.wf32(sample + 0x14, threshold - 0.1)
        t.wf32(sample + 0x10, 0.0)
        t.wf32(sample + 0x18, 0.0)
        t.w8(sample + 8, 0)
        t.w8(sample + 10, 1)
    t.args(r3=rng.getrandbits(32), r4=array, r5=start)


def forecast_step(ctx):
    control = u32(ctx, 0x825EAB28)
    step = u32(ctx, control) + 1
    put32(ctx, control, step)
    target = u32(ctx, control + 4)
    mode = u32(ctx, control + 8)
    sample = ctx.r(3)
    # Touch both clocks and w lanes as a real step does, allowing callers to
    # observe the exact number of extrapolations without changing predicates.
    for off in (0, 4, 0x1C, 0x2C):
        value = struct.unpack(">f", ctx.read(sample + off, 4))[0]
        ctx.write(sample + off, struct.pack(">f", value + 0.125))
    if step == target:
        if mode == 0:
            ctx.write(sample + 8, b"\1")
        elif mode == 1:
            ctx.write(sample + 0x14, struct.pack(">f", -10.0))
            ctx.write(sample + 0x24, struct.pack(">f", -1.0))
        elif mode == 2:
            ctx.write(sample + 0x10, struct.pack(">f", float("nan")))
        elif mode == 3:
            put32(ctx, u32(ctx, control + 12), u32(ctx, control + 16))


def debug_log(ctx):
    if ctx.read(ctx.r(3), 9) == b"Could not":
        assert ctx.r(4) == 120, "forecast limit log has wrong sample count"


FORECAST_CALLS = {
    "BallPredict_IsFiniteXYZ": run(args=("r3",), deref={"r3": 16}),
    "BallPredict_StepSample": model(forecast_step, args=("r3", "r4"), deref={"r3": 0x50}),
    "nop_8240E6D0": model(debug_log, args=("r3",)),
}


def forecast_inputs(t):
    rng = t.rng
    height, radius = world(t)
    floor = f32(height - radius)
    control = t.alloc(32, "forecast script")
    t.w32(0x825EAB28, control)
    sample = t.alloc(0x50, "sample", floats=[(0, 2), (0x10, 16)])
    result = t.alloc(4, "outcome")
    t.floats(sample, 2, 0, 10)
    t.floats(sample + 0x10, 16, -3, 3)
    t.wf32(sample + 0x14, 3.0)
    t.wf32(sample + 0x18, rng.choice([-2.0, -0.0, 0.0, 2.0]))
    t.wf32(sample + 0x24, rng.choice([-1.0, 0.0, 1.0]))
    t.w8(sample + 8, 0)
    mode = t.index % 8
    if mode == 0:
        t.w8(sample + 8, rng.choice([1, 255]))
    elif mode == 1:
        t.wf32(sample + 0x14, rng.choice([floor - 0.01, floor, floor + 0.01]))
        t.wf32(sample + 0x24, -1.0)
        t.w8(sample + 8, rng.choice([0, 1]))
    elif mode == 2:
        t.wf32(sample + rng.choice([0x10, 0x14, 0x18, 0x20, 0x24, 0x28]), rng.choice([float("nan"), float("inf"), float("-inf")]))
    elif mode == 5:
        t.wf32(sample + 0x14, floor - 0.1)
        t.wf32(sample + 0x24, 1.0)
    t.w32(control, 0)
    t.w32(control + 4, 1000 if mode == 6 else rng.choice([1, 3, 119, 120]))
    t.w32(control + 8, mode % 4)
    t.w32(control + 12, result)
    t.w32(control + 16, rng.choice([1, 2, 3, 17]))
    t.args(r3=sample, r4=result, r5=rng.getrandbits(32))
