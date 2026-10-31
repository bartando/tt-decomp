"""0x82101668: fixed seven-bit magnitude and failure of either read."""
from liftcheck.spec import *
FUNCTION = "datBitBuffer_ReadS8"
ADDRESS = 0x82101668
SOURCE = "src/rage/net/dat_bit_buffer.cpp"
TRIALS = 400
CALLS = {"datBitBuffer_ReadU32": run(), "datBitBuffer_ReadU8": run()}
def inputs(t):
    bb = t.alloc(0x28, "buffer", ctype="datBitBufferView")
    data = t.alloc(32, "data")
    dst = t.alloc(4, "destination")
    t.w32(bb + 4, data)
    t.w32(bb + 0x10, t.rng.choice([0, 1, 2, 7, 8, 9, 128]))
    t.w32(bb + 0x18, t.rng.randrange(8))
    t.w32(bb + 0x1C, 0)
    t.args(r3=bb, r4=dst, r5=t.u32())
