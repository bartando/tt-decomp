"""Shared randomized setup for the scalar and vector parameter writers."""
def inputs(t, vector):
    r = t.rng
    context = t.alloc(32, "context")
    state = t.alloc(0x4100, "primary state and dirty bits")
    dirty = t.alloc(0x4000, "secondary dirty bits")
    entries = [t.alloc(0x20000, "primary descriptors"), t.alloc(0x20000, "secondary descriptors")]
    values = [t.alloc(0x1010, "primary values"), t.alloc(0x1010, "secondary values")]
    entry_header = t.alloc(4, "secondary descriptor pointer")
    value_header = t.alloc(4, "secondary value pointer")
    bank = r.randrange(2)
    index = r.choice([0, 1, 0x3fff, r.randrange(0x4000)])
    bit = r.choice([0, 1, 7, 8, 0x1ffff, r.randrange(0x20000)])
    handle = (index << 18) | (bit << 1) | bank
    slot = r.randrange(1, 255)
    t.w32(context, state)
    t.w32(context + 16, r.choice([0, 1, t.u32()]))
    t.w32(state + 256, dirty)
    t.w32(state + 264, entries[0])
    t.w32(state + 268, entry_header)
    # Scalar stvewx selects a lane from stack garbage for misaligned banks.
    # Real scalar banks consist of aligned 16-byte slots.
    offsets = [r.randrange(16), r.randrange(16)] if vector else [0, 0]
    t.w32(state + 296, values[0] + offsets[0])
    t.w32(state + 300, value_header)
    t.w32(entry_header, entries[1])
    t.w32(value_header, values[1] + offsets[1])
    for i in range(2):
        t.w32(entries[i] + index * 8 + 4, (t.u32() & 0xffff0000) | (slot if i == bank else slot + 1))
    if vector:
        value = t.alloc(32, "vector source")
        # Alias the counter sometimes: the original decrements before loading.
        source = context + 16 if r.randrange(5) == 0 else value
        t.args(r3=context, r4=handle, r5=source + r.randrange(16))
    else:
        t.args(r3=context, r4=handle, f1=r.choice([0.0, -0.0, 1.0, r.uniform(-1e8, 1e8)]))
