"""Body guards, nonzero root velocities, arbitrary W, aliasing and empty chains."""
def velocity_inputs(t):
    rng = t.rng
    count = rng.choice((-3, 0, 1, 2, 4, 8))
    data = t.alloc(192, "jointDataAndGuards")
    bodies = []
    for i in range(max(1, count)):
        body = t.alloc(0x180, f"body{i}AndGuards") + 16
        t.floats(body, 0x160 // 4, -20, 20)
        bodies.append(body)
        t.w32(data + 40 + i * 4, body)
    t.w32(data + 4, count)
    value = t.alloc(48, "inputAndGuards") + 16
    t.floats(value, 4, -20, 20)
    if t.index % 3 == 0:
        value = rng.choice(bodies) + rng.choice((0xC0, 0x110, 0x120, 0x130, 0x140))
    if t.index % 7 == 0:
        # Repeated body pointers must see the previous iteration's changes.
        for i in range(max(1, count)):
            t.w32(data + 40 + 4 * i, bodies[0])
    if t.index % 5 == 0:
        addr = rng.choice(bodies) + rng.choice((0xC0, 0x110, 0x120)) + 4 * rng.randrange(4)
        t.w32(addr, rng.choice((0, 0x80000000, 1, 0x807FFFFF, 0x00800000,
                               0x7F800000, 0xFF800000, 0x7FC00000)))
    if t.index % 19 == 0 and count > 0:
        # Amplify a denormal position into a visible cross term if VMX input
        # flushing is accidentally removed. Ordinary velocities swallow it.
        value = t.alloc(16, "flushProbeVelocity")
        for lane in range(4):
            t.wf32(value + lane * 4, 1e38 if lane == 1 else 0)
        for body in bodies:
            for offset in (0xC0, 0x110, 0x120):
                for lane in range(4):
                    t.wf32(body + offset + lane * 4, 0)
            t.w32(body + 0xC8, 0x007FFFFF)
    t.args(r3=data, r4=value)
