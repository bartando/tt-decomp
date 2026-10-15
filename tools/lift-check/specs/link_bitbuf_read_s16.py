"""datBitBuffer::ReadSigned<s16> (0x820D7970): sign bit + 15-bit magnitude, both readers run."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "datBitBuffer_ReadS16"
ADDRESS = 0x820D7970
SOURCE = "src/rage/net/dat_bit_buffer.cpp"

CALLS = {
    "datBitBuffer_ReadU32": run(),
    "datBitBuffer_ReadU16": run(),
}


def inputs(t):
    rng = t.rng
    nbytes = rng.choice([4, 8, 16])
    data = t.alloc(nbytes + 8, "data")
    bb = t.alloc(0x20, "bb")
    offset = rng.choice([0, rng.randrange(8)])
    limit = nbytes * 8 - offset
    cursor = rng.choice([0, rng.randrange(0, limit), limit - 16, limit - 15, limit - 1])
    t.w32(bb + 0x04, data)
    t.w32(bb + 0x10, limit)
    t.w32(bb + 0x18, offset)
    t.w32(bb + 0x1C, max(0, cursor))
    out = t.alloc(2, "out")
    t.args(r3=bb, r4=out, r5=rng.choice([16, 8, 3]))
