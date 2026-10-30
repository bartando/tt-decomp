"""XMA lock completion, 0x8246B860 (descriptive SDK name).

Executes the original MMIO read and context snapshot code without stubs or ignored
memory. Covers already locked, zero/one/multiple streams, every valid-input mask,
busy context at any index, little-endian register values including upper bits,
and preservation of all snapshot/cached metadata outside consumed slots.
The explicitly mapped register is stable during each invocation.
"""
from liftcheck.spec import *

FUNCTION = "XmaDecoder_TryCompleteLock"
ADDRESS = 0x8246B860
SOURCE = "src/rage/audio/xma_source.cpp"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    decoder = t.alloc(12, "decoder", ctype="XmaDecoderLayout")
    count = rng.choice([0, 1, 1, 2, 3, 6])
    contexts = t.alloc(max(1, count) * 96, "contexts")
    t.w32(decoder, count)
    t.w32(decoder + 4, (t.u32() & ~0x20000) | rng.choice([0, 0, 0, 0x20000]))
    t.w32(decoder + 8, contexts)
    t.map(0x7FEA1000, 0x1000, "xmaMMIO")
    current = rng.choice([0, 1, 0x1ff, 0x200, 0x3ff, 0xffff, t.u32()])
    # Include words that cannot match a uint16 context ID, without truncating them.
    t.put(0x7FEA1818, (current ^ 0x200).to_bytes(4, "little"))
    busy = rng.randrange(count) if count and current <= 0xffff and rng.randrange(2) else -1
    alias = rng.randrange(count) if count and current > 0xffff else -1
    for i in range(count):
        context = contexts + i * 96
        hardware = t.alloc(48, f"hardware{i}")
        t.w32(context + 64, hardware)
        t.w16(context + 76, current if i in (busy, alias) else (current + i + 1) & 0xffff)
        valid = rng.randrange(4)
        t.w32(hardware, (t.u32() & ~0x300000) | (valid << 20))
    t.args(r3=decoder)
