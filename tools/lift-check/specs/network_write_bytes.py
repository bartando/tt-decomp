"""0x82260738: bulk bit-stream writes with COW/growth and surrounding bits."""
from liftcheck.spec import *
from specs.link_bitbuf_begin_packet import CALLS, make_buffer
FUNCTION = "netStream_WriteString"
ADDRESS = 0x82260738
SOURCE = "src/rage/net/dat_bit_buffer.cpp"
TRIALS = 400

def inputs(t):
    bb, max_bits, size = make_buffer(t)
    cursor = t.rng.choice([0, size, max_bits - 1, max_bits - 8])
    t.w32(bb + 0x20, cursor)
    source = t.alloc(64, "source")
    t.args(r3=bb, r4=source, r5=t.rng.choice([0, 1, 2, 3, 16, 32]))
