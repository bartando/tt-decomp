"""All format masks, raw float bits, fallback counts, aliased matrix streams,
repeated/noncontiguous slots and unaligned lvx/stvx. No ignored memory ranges."""
FUNCTION = 'game_9AA0'
ADDRESS = 0x82159AA0
SOURCE = 'src/game/pong_render.cpp'
TRIALS = 1400
EXTERNS = {'g_shaderMatrixTransposeMasks': 0x8202F0A0}


def inputs(t):
    r = t.rng
    table = t.alloc(0x120, 'table')
    entries = t.alloc(0x180, 'descriptors')
    bank_base = t.alloc(0x800, 'bankAndGuards') + 16
    bank = bank_base + r.randrange(16)
    source = t.alloc(0x400, 'sourceAndGuards') + r.randrange(16)
    if t.index % 3 == 0:
        source = bank_base + r.choice([0, 16, 32, 48]) + r.randrange(16)
    index = r.randrange(4)
    bit = r.choice([1, 7, 8, 15, 31, 120, 1998, r.randrange(1999)])
    count = r.choice([0, 0, 1, 2, 3, 4, 7, 9, -1, -2])
    if count < 0:
        bit = 15  # Wrapped unsigned end skips the loop.
    t.w32(table + 0x100, entries)
    t.w32(table + 0x108, bank)
    header = entries + index * 8
    default = r.randrange(10)
    t.w32(header, (t.u32() & ~0xFFFC) | (default << 2))
    for i in range(10):
        descriptor = header + (i + 1) * 8
        t.w32(descriptor, (t.u32() & ~0x70) | (r.randrange(8) << 4))
        t.w32(descriptor + 4, (t.u32() & 0xFFFF0000) | r.choice([0, 1, 2, r.randrange(80)]))
    if t.index % 5 == 0:
        # Earlier output overwrites later input, but each matrix is snapshotted.
        source = bank_base + r.randrange(16)
        t.w32(header + 12, 1)
        t.w32(header + 20, 5)
        count = 3
    t.args(r3=table, r4=(index << 18) | (bit << 1) | r.randrange(2),
           r5=source, r6=count)
