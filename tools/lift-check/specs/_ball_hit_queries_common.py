"""Leaf-query fixtures: wrapped rings, strict boundaries, NaNs and signed zero."""
import math
import struct


def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def inputs(t, kind):
    rng = t.rng
    data = t.alloc(0x2800, "prediction")
    count = rng.choice([0, 1, 2, 3, 8, 119, 120])
    tail = rng.choice([0, 1, 117, 118, 119])
    t.w32(data + 0x25A4, tail)
    t.w32(data + 0x25A8, count)
    width = f32(rng.choice([0.0, 1.52, 2.0, 2.5]))
    height = f32(rng.choice([0.0, 0.76, 1.0]))
    length = f32(rng.choice([0.0, 2.74, 3.0]))
    table = t.alloc(0x20, "table")
    t.wf32(table + 0x10, width)
    t.wf32(table + 0x14, height)
    t.wf32(table + 0x18, length)
    t.w32(0x8271A304, table)
    mode = t.index % 8
    for i in range(120):
        sample = data + 0x20 + ((tail + i + 1) % 120) * 0x50
        x = rng.choice([-width * 0.5, width * 0.5, -2.0, 2.0, 0.0, -0.0, float("nan")])
        y = rng.choice([height, 1.0, 0.0, -0.0, -1.0, float("nan")])
        z = rng.choice([-length * 0.5, length * 0.5, -2.0, 2.0, 0.0, -0.0, float("nan")])
        if mode in (0, 1, 4):
            y = 1.0
        if mode == 0:
            net = 0
            bounced = 0
        elif mode == 1:
            net = int(i == count - 1)
            bounced = 1
        elif mode == 2:
            net = 255
            bounced = 255
            y = 0.0
        else:
            net = rng.choice([0, 0, 1, 255])
            bounced = rng.choice([0, 0, 1, 255])
        t.w8(sample + 8, bounced)
        t.w8(sample + 9, net)
        t.wf32(sample + 0x10, x)
        t.wf32(sample + 0x14, y)
        t.wf32(sample + 0x18, z)
        for off in (0x20, 0x24, 0x28):
            t.wf32(sample + off, rng.choice([-2.0, -0.0, 0.0, 2.0, float("nan")]))
    side = rng.choice([0, 1, 2, 255, 0x100, 0x101, 0x10000000])
    start = rng.choice([0, 1, max(0, count - 1), count, count + 1])
    if kind == "departing" and start >= count and rng.random() < 0.5:
        t.w32(0x8271A304, 0)  # the original never dereferences the table here
    if kind == "forecast":
        last = data + 0x20 + ((tail + count) % 120) * 0x50
        x_edge = f32(math.fma(width, 0.5, f32(0.1)))
        z_edge = f32(math.fma(length, 0.5, f32(0.1)))
        t.wf32(last + 0x10, rng.choice([-x_edge, x_edge, -x_edge - 0.001, x_edge + 0.001, 0.0, -0.0, float("nan")]))
        t.wf32(last + 0x14, rng.choice([f32(height - f32(0.1)), height - 0.2, height, 1.0, float("nan")]))
        t.wf32(last + 0x18, rng.choice([-z_edge, z_edge, -z_edge - 0.001, z_edge + 0.001, -1.0, -1.001, -0.5, 0.0, -0.0, float("nan")]))
        t.args(r3=data, r4=side)
    elif kind == "bounce":
        t.args(r3=data, r4=side, r5=start)
    else:
        t.args(r3=data, r4=start)
