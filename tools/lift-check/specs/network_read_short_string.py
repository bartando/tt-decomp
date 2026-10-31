"""0x82260A70: fixed-width lookahead then rewind to the string terminator."""
from liftcheck.spec import *
FUNCTION = "datBitBuffer_ReadShortString"
ADDRESS = 0x82260A70
SOURCE = "src/rage/net/dat_bit_buffer.cpp"
TRIALS = 400
CALLS = {"snBitStream_ReadString": run()}
def inputs(t):
    bb = t.alloc(0x28, "buffer", ctype="datBitBufferView")
    data = t.alloc(32, "data")
    # Include empty, embedded terminator and full-width strings.
    for i in range(32): t.w8(data + i, t.rng.choice([0, 0, 65, 255, t.rng.randrange(256)]))
    dst = t.alloc(32, "destination")
    t.w32(bb + 4, data)
    t.w32(bb + 0x10, t.rng.choice([0, 7, 8, 32, 127, 128, 160]))
    t.w32(bb + 0x18, t.rng.randrange(8))
    t.w32(bb + 0x1C, 0)
    t.args(r3=bb, r4=dst)
