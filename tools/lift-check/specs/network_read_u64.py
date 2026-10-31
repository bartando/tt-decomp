"""0x822609F0: low-word-first u64, including failure of either constituent read."""
from liftcheck.spec import *
FUNCTION = "datBitBuffer_ReadU64"
ADDRESS = 0x822609F0
SOURCE = "src/rage/net/dat_bit_buffer.cpp"
TRIALS = 400
CALLS = {"datBitBuffer_ReadU32": run()}
def inputs(t):
    bb = t.alloc(0x28, "buffer", ctype="datBitBufferView")
    data = t.alloc(32, "data")
    dst = t.alloc(8, "destination")
    t.w32(bb + 4, data)
    t.w32(bb + 0x10, t.rng.choice([0, 1, 31, 32, 33, 63, 64, 128]))
    t.w32(bb + 0x18, t.rng.randrange(8))
    t.w32(bb + 0x1C, 0)
    t.args(r3=bb, r4=dst)
