"""Shader parameter upload: two dirty banks, eight categories, override and clears.

Exercise empty/sparse/dense masks, all 64 bit positions, runs across bit 31/32,
multiple dirty words, all register/count fields, descriptor masking, VMX address
rounding, signed/unsigned saturation, NaN/infinities, defaults merged into Y/Z/W,
and cache-line clears with offsets inside the allocation.

Limits: allocated/valid descriptors and pointers; at most 16 dirty words per bank
(the 128-byte dirty-line capacity). Device/value/layout arrays are disjoint.
Upload callees are void stubs: compare all argument registers and the initialized
16-byte vector, not the callees' implementations. Packed signed counts 2..4 are
checked as arguments only: the original initializes just one vector of its stack
buffer, so any additional callee reads would consume indeterminate stack bytes.
VS/PS float destinations may overlap each other, as in the original. Exclude
only the emulator's private XER-trampoline r0 spill (machine.py _TRAMP_CODE),
which srad writes on the original side. No game memory or float tolerance is
excluded; copies and conversions compare exactly.
"""
from liftcheck.spec import *

FUNCTION = "rage_6370"
ADDRESS = 0x82446370
SOURCE = "src/rage/rage_grm.cpp"
IGNORE = [(0xFFFF8000, 4)]  # emulator-private scratch, not a game write

CALLS = {
    name: stub(ret="void", args=("r3", "r4", "r5", "r6"), deref={"r5": 16})
    for name in ("rage_6BA0_h", "rage_6BF8_h", "rage_6C50_h", "rage_6CA0_h")
}
CALLS["rage_9940"] = stub(ret="void", args=("r3", "r4", "r5"))

EDGE_BITS = [
    0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x807FFFFF,
    0x3F000000, 0xBF000000, 0x3FF33333, 0xBFF33333,
    0x4EFFFFFF, 0x4F000000, 0x4F000001, 0xCEFFFFFF, 0xCF000000,
    0xCF000001, 0x4F7FFFFF, 0x4F800000, 0x4F800001,
    0x7F800000, 0xFF800000, 0x7FC00000, 0xFFC01234, 0x7F800001,
]


def inputs(t):
    rng = t.rng
    state_base = t.alloc(0x340, "stateWithCacheLinePadding", align=128)
    state = state_base + rng.choice([0, 0, 8, 16, 120])
    second_base = t.alloc(0x100, "secondDirtyWithCacheLinePadding", align=128)
    second_dirty = second_base + rng.choice([0, 0, 8, 16, 120])
    device = t.alloc(0x6000 + 16, "device") + rng.choice([0, 4, 8, 12])
    counts = [rng.choice([0, 1, 1, 2, 3, 16]) for _ in range(2)]
    mode = rng.randrange(12)
    if mode == 0:
        counts = [0, 0]
    t.w32(state + 256, second_dirty)
    t.w32(state + 288, counts[0])
    t.w32(state + 292, counts[1])
    t.w32(state + 700, device)

    tables, values = [], []
    for bank in range(2):
        table = t.alloc(8 * 16, f"metadata{bank}")
        data = t.alloc(0x500, f"values{bank}") + rng.randrange(16)
        tables.append(table)
        values.append(data)
        for index in range(16):
            t.w32(table + index * 8 + 4, (t.u32() & 0xFFFF0000) | rng.randrange(64))
        for offset in range(0, 0x480, 4):
            t.w32((data & ~15) + offset, rng.choice(EDGE_BITS) if rng.random() < 0.8 else t.u32())
    t.w32(state + 264, tables[0])
    t.w32(state + 296, values[0])
    for offset, value in ((268, tables[1]), (300, values[1])):
        header = t.alloc(4, f"header{offset}")
        t.w32(header, value)
        t.w32(state + offset, header)

    def mask():
        if mode == 1:
            return 0
        if mode == 2:
            return 0xFFFFFFFFFFFFFFFF
        if mode == 3:
            return rng.choice([0x8000000000000000, 1, 0x0000000180000000,
                               0xAAAAAAAAAAAAAAAA, 0x5555555555555555])
        result = 0
        for _ in range(rng.randrange(1, 7)):
            result |= 1 << rng.randrange(64)
        return result

    # Dirty words may be nonzero beyond wordCount; the entire containing cache
    # line is still cleared. Test distinct snapshots for every category.
    dirty_masks = [[mask() for _ in range(16)] for _ in range(2)]
    for bank, base in enumerate((state, second_dirty)):
        for word, bits in enumerate(dirty_masks[bank]):
            t.w64(base + word * 8, bits)

    def layout(name):
        obj = t.alloc(0x54, name)
        defaults = t.alloc(16 * 256 + 16, name + ".defaults") + rng.randrange(16)
        t.w32(obj + 80, defaults)
        for bank in range(2):
            bindings = t.alloc(max(counts[bank], 1) * 64 * 16, name + f".bindings{bank}")
            t.w32(obj + 64 + bank * 4, bindings)
            for index in range(max(counts[bank], 1) * 64):
                binding = bindings + index * 16
                t.w32(binding, rng.randrange(16) << 18 | rng.getrandbits(18))
                for offset in (4, 8):
                    flags = t.u32()
                    first = rng.choice([0, 1, 2, 3, 4, 7, 251, 252, 253, 254, 255, 256,
                                        511, 512, 513, 767, 768, 1020, 1023])
                    t.w32(binding + offset, (flags & ~0x3FF) | first)
            for category in range(8):
                masks = t.alloc(16 * 8, name + f".masks{bank}.{category}")
                t.w32(obj + (bank * 8 + category) * 4, masks)
                for word in range(16):
                    bits = mask()
                    # Dense trials select one category to keep call counts bounded;
                    # other modes mix categories and filtered-out dirty bits.
                    if mode == 2:
                        bits = 0xFFFFFFFFFFFFFFFF if category == rng.randrange(8) else 0
                    if mode >= 4:
                        bits |= dirty_masks[bank][word] & rng.getrandbits(64)
                    t.w64(masks + word * 8, bits)
        return obj

    local = layout("localLayout")
    override = layout("overrideLayout")
    t.w32(state + 536, local)
    t.w32(state + 696, rng.choice([0, 1, 0x80000000]))
    t.w32(0x825B1F70, rng.choice([0, 1, 0xFFFFFFFF]))
    t.w32(0x825E784C, override)
    t.args(r3=state)
