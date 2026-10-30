"""All VM tags, dirty boolean padding, signed words and float32 bit patterns.

atoi is a boundary with randomized returns: check the original payload pointer,
its complete text and return forwarding, rather than retesting the CRT. Tag 0
is passed directly as text, even when its first chunk links to another chunk.
Float cases include NaNs, infinities, subnormals and both int32 limits. No
ignored bytes, tolerance or FPSCR comparison; the contract is the integer result.
"""
from liftcheck.spec import *

FUNCTION = "swfValueToInteger"
ADDRESS = 0x823FA5C8
SOURCE = "src/rage/swf.cpp"
TRIALS = 1200
CALLS = {0x82432120: stub(ret=lambda c: c.rng.getrandbits(32), args=("r3",))}

FLOAT_BITS = (
    0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x00800000,
    0x3F400000, 0xBF400000, 0x3FE00000, 0xBFE00000,
    0x4EFFFFFF, 0x4F000000, 0x4F000001, 0xCEFFFFFF, 0xCF000000, 0xCF000001,
    0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
    0x7FC12345, 0xFFC12345, 0x7F812345, 0xFF812345,
)
TAGS = (0, 1, 2, 3, 4, 5, 6, 7, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)


def inputs(t):
    r = t.rng
    value = t.alloc(8, "value")
    # Interleave guaranteed float edges with every tag and arbitrary bits.
    tag = 4 if t.index % 2 == 0 else TAGS[(t.index // 2) % len(TAGS)]
    t.w32(value + 4, tag)
    if tag in (0, 1):
        text = r.choice((b"", b"0", b"-17", b" +42tail", b"2147483647", b"-2147483648", b"nonsense"))
        chunk = t.alloc(16, "textOrFirstChunk", fill=text + b"\0")
        t.w32(chunk + 12, t.alloc(16, "unusedNextChunk", fill=b"98765\0"))
        t.w32(value, chunk)
    elif tag == 2:
        t.w32(value, t.u32() | 0x00FFFFFF)
        t.w8(value, r.choice((0, 1, 2, 127, 128, 255)))
    elif tag == 3:
        t.w32(value, r.choice((0, 1, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, t.u32())))
    elif tag == 4:
        bits = FLOAT_BITS[(t.index // 2) % len(FLOAT_BITS)] if t.index % 2 == 0 else t.u32()
        t.w32(value, bits)
    else:
        t.w32(value, t.u32() | 1)
    t.args(r3=value)
