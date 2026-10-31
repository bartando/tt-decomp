"""0x824090D0: signed-byte ELF-style string hash, including high-byte keys."""
from liftcheck.spec import *
FUNCTION = "localizedTextHash"
ADDRESS = 0x824090D0
SOURCE = "src/rage/data/localized_text.cpp"
TRIALS = 400
def inputs(t):
    key = t.alloc(128, 'key')
    for i in range(128): t.w8(key + i, t.rng.randrange(1,256))
    t.w8(key + t.rng.choice([0,1,2,7,31,63,127]), 0)
    t.args(r3=key)
