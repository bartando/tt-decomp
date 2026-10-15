"""datBitBuffer::ReadUnsigned<u8> (0x820D7A08): bit-cursor read into a u8."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "datBitBuffer_ReadU8"
ADDRESS = 0x820D7A08
SOURCE = "src/rage/net/dat_bit_buffer.cpp"


def inputs(t):
    rng = t.rng
    nbytes = rng.choice([4, 8, 16, 40])
    data = t.alloc(nbytes + 8, "data")
    bb = t.alloc(0x20, "bb")
    limit = nbytes * 8
    offset = rng.choice([0, 0, rng.randrange(8), rng.randrange(16)])
    limit -= offset
    cursor = rng.randrange(0, max(1, limit))
    bits = rng.choice([0, 1, 2, 7, 8, 9, 15, 16, 17, 24, 31, 32, rng.randrange(0, 33), -1, limit - cursor + 1])
    if rng.random() < 0.05:
        cursor = limit  # bits == 0 at the very end reaches the garbage path; keep bits > 0
        bits = rng.choice([1, 8])
    t.w32(bb + 0x04, data)
    t.w32(bb + 0x10, limit)
    t.w32(bb + 0x18, offset)
    t.w32(bb + 0x1C, cursor)
    out = t.alloc(1, "out")
    t.args(r3=bb, r4=out, r5=bits & 0xFFFFFFFF)
