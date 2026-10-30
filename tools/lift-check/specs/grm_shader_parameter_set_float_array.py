"""Array header fallback length, four-scalar snapshots, dirty bit boundaries.

Explicit/default counts 0..19; all dirty bit offsets, odd dirty-byte offsets,
noncontiguous/repeated output slots, unaligned sources and source/value aliases.
Valid 16-byte aligned value banks; arbitrary scalar bits preserved exactly.
Descriptors and table do not alias values. No calls, tolerance or ignored bytes.
"""
FUNCTION = 'grmShaderParameter_SetFloatArray'
ADDRESS = 0x82159908
SOURCE = 'src/rage/rage_grm.cpp'
TRIALS = 1000


def inputs(t):
    table = t.alloc(0x120, 'parameter table')
    entries = t.alloc(0x300, 'descriptors')
    bank = t.alloc(0x400, 'value bank')
    source = t.alloc(112, 'unaligned source and guards') + t.rng.randrange(16)
    index = t.rng.randrange(4)
    bit = t.pick([0, 7, 8, 15, 31, 127, 2000, 2028, t.rng.randrange(2029)])
    explicit = t.pick([0, 0, 1, 2, 3, 4, 5, 7, 8, 9, 17, 19])
    default = t.rng.randrange(20)
    t.w32(table + 0x100, entries)
    t.w32(table + 0x108, bank)
    header = entries + index * 8
    t.w32(header, (t.u32() & ~0xFFFC) | default << 2)
    slots = [t.rng.randrange(32) for _ in range(20)]
    for k, slot in enumerate(slots):
        t.w32(header + 8 * (k + 1) + 4, (t.u32() & 0xFFFF0000) | slot)
    if t.index % 3 == 0:
        source = bank + t.pick([0, 4, 16, 20, 32, 48])
    if t.index % 10 == 0:
        # First store overwrites the fourth source scalar. Only the original's
        # four-word snapshot keeps the last write correct, independent of RNG.
        explicit = 4
        source = bank + 4
        for k in range(4):
            t.w32(header + 8 * (k + 1) + 4, (t.u32() & 0xFFFF0000) | (k + 1))
    t.args(r3=table, r4=(index << 18) | (bit << 1) | t.rng.randrange(2), r5=source, r6=explicit)
