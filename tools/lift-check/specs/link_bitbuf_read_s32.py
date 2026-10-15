"""datBitBuffer::ReadSigned<s32> (0x82260E18): sign bit, then bits - 1 of magnitude."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "datBitBuffer_ReadS32"
ADDRESS = 0x82260E18
SOURCE = "src/rage/net/dat_bit_buffer.cpp"

CALLS = {"datBitBuffer_ReadU32": run()}


def inputs(t):
    rng = t.rng
    nbytes = rng.choice([4, 8, 16])
    data = t.alloc(nbytes + 8, "data")
    bb = t.alloc(0x28, "bb")
    offset = rng.choice([0, rng.randrange(8)])
    limit = nbytes * 8 - offset
    t.w32(bb + 0x04, data)
    t.w32(bb + 0x10, limit)
    t.w32(bb + 0x18, offset)
    bits = rng.choice([1, 2, 8, 16, 31, 32, 33])
    # with the cursor at the limit after the sign bit, a 0-bit read reaches the
    # original's uninitialised-pointer path; keep a bit after the sign
    cursor = rng.choice([0, rng.randrange(0, max(1, limit - 1)), max(0, limit - bits - 1), limit - 2])
    t.w32(bb + 0x1C, cursor)
    t.args(r3=bb, r4=t.alloc(4, "out"), r5=bits)
