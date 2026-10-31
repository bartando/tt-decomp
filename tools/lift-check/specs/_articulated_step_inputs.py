"""Articulated body arrays with independent saved/current states and guards."""
def bodies(t):
    rng = t.rng
    count = rng.choice((-3, 0, 1, 2, 4, 8))
    data = t.alloc(0x240, "jointDataAndGuards")
    t.w32(data + 4, count)
    result = []
    for i in range(max(1, count)):
        body = t.alloc(0x480, f"body{i}AndGuards") + 16
        t.floats(body, 0x460 // 4, -30, 30)
        result.append(body)
        t.w32(data + 40 + i * 4, body)
    if t.index % 7 == 0:
        for i in range(max(1, count)):
            t.w32(data + 40 + i * 4, result[0])
    return data, result
