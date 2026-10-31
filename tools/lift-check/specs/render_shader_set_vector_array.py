"""Array header fallback, MSB-first dirty bits, per-vector lvx/stvx and counter wrap.
Disjoint descriptors/table; repeated/noncontiguous output slots and input/output
aliases. Source and value-bank offsets exercise lvx/stvx 16-byte alignment.
"""
FUNCTION = 'game_A670'
ADDRESS = 0x8215A670
SOURCE = 'src/game/pong_render.cpp'
TRIALS = 1400
# The symbol map splits this leaf at an internal loop instruction.
EXTRA_RANGES = [(0x8215A6E8, 0x8215A73C)]


def inputs(t):
    r = t.rng
    table = t.alloc(0x120, 'table')
    entries = t.alloc(0x180, 'descriptors')
    bankBase = t.alloc(0x500, 'bankAndGuards') + 16
    bank = bankBase + r.randrange(16)
    source = t.alloc(0x180, 'sourceAndGuards') + r.randrange(16)
    if t.index % 3 == 0:
        source = bankBase + r.choice([0, 16, 32]) + r.randrange(16)
    index = r.randrange(4)
    bit = r.choice([1, 7, 8, 15, 31, 120, 1998, r.randrange(1999)])
    count = r.choice([0, 0, 1, 2, 3, 4, 7, 9, 11, -1, -2])
    if count < 0:
        bit = 15  # unsigned end wraps below the initial bit, so no vector read.
    t.w32(table + 0x100, entries)
    t.w32(table + 0x108, bank)
    header = entries + index * 8
    default = r.randrange(12)
    t.w32(header, (t.u32() & ~0xFFFC) | (default << 2))
    for i in range(12):
        slot = r.choice([0, 1, 2, r.randrange(48)])
        t.w32(header + 8 * (i + 1) + 4, (t.u32() & 0xFFFF0000) | slot)
    t.w32(0x825EBC40, table)
    t.w32(0x825EBC54, r.choice([0, 0xFFFFFFFF, t.u32()]))
    if t.index % 5 == 0:
        # The first destination overlaps the second input: snapshot one vector
        # at a time, rather than copying the whole array before writing.
        source = bankBase + r.randrange(16)
        t.w32(header + 12, 1)
        t.w32(header + 20, 2)
        count = 3
    t.args(r3=(index << 18) | (bit << 1) | r.randrange(2), r4=source, r5=count)
