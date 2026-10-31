"""0x82260688: write at most 15 bytes and always attempt the trailing zero."""
from liftcheck.spec import *
from specs.link_bitbuf_begin_packet import CALLS as BASE_CALLS, make_buffer
FUNCTION = "datBitBuffer_WriteShortString"
ADDRESS = 0x82260688
SOURCE = "src/rage/net/dat_bit_buffer.cpp"
TRIALS = 400
CALLS = dict(BASE_CALLS, netStream_WriteString=run())

def inputs(t):
    bb, max_bits, size = make_buffer(t)
    t.w32(bb + 0x20, t.rng.choice([0, size, max_bits - 1, max_bits, max_bits + 8]))
    source = t.alloc(32, "source")
    for i in range(32): t.w8(source + i, t.rng.randrange(1, 256))
    t.w8(source + t.rng.choice([0, 1, 2, 14, 15, 16, 31]), 0)
    t.args(r3=bb, r4=source)
