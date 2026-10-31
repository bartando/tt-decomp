"""0x82260AF0: aligned/unaligned bulk reads, clamping and cursor updates."""
from liftcheck.spec import *
FUNCTION = "snBitStream_ReadString"
ADDRESS = 0x82260AF0
SOURCE = "src/rage/net/dat_bit_buffer.cpp"
TRIALS = 400

def inputs(t):
    bb = t.alloc(0x28, "buffer", ctype="datBitBufferView")
    data = t.alloc(128, "data")
    dst = t.alloc(96, "destination")
    cursor = t.rng.randrange(32)
    size = t.rng.choice([cursor, cursor - 1, cursor + 7, cursor + 8, cursor + 128, cursor + 511])
    t.w32(bb + 4, data)
    t.w32(bb + 0x10, size)
    t.w32(bb + 0x18, t.rng.randrange(16))
    t.w32(bb + 0x1C, cursor)
    count = t.rng.choice([-1, 0, 1, 2, 16, 64])
    t.args(r3=bb, r4=dst, r5=count & 0xFFFFFFFF)
