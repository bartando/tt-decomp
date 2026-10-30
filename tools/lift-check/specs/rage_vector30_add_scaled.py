"""Weighted 30-component accumulation, including overlapping buffers."""
FUNCTION = "rage::vector30AddScaled"
ADDRESS = 0x82231EA0
SOURCE = "src/rage/math/rage_math.cpp"
TRIALS = 1200


def inputs(t):
    rng = t.rng
    storage = t.alloc(512, "storage")
    destination = storage + 192
    source = destination + rng.choice([-124, -120, -40, -4, 0, 4, 40, 120, 124])
    kind = rng.randrange(4)
    for i in range(128):
        value = rng.uniform(-100, 100)
        if kind == 0:
            value = rng.choice([-1.0, 1.0]) * (1.0 + rng.randrange(32) * 2**-20)
        elif kind == 1:
            value = rng.choice([0.0, -1.0, 1.0, 16.0])
        t.wf32(storage + 4 * i, value)
    weight = rng.choice([0.0, 1.0, -1.0, rng.uniform(-10, 10)])
    t.args(r3=destination, r4=source, f1=weight)
