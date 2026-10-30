"""0x821AAEE8: append a big-endian audio header and byte-counted payload.

All 256 parameter counts, count+1 byte wrap, class/ID truncation, nonzero
write indices and distinct payload/guard words. Zero count permits a null
payload. Also exercises a source overlapping the destination to check forward
word copying. Payloads may also reference the live write index, checking that
it is published before copying. Exact writes and write-index comparison, no calls or ignores.
Synthetic sufficiently large linear ring storage; this function does not wrap.
"""
from liftcheck.spec import *

FUNCTION = "rage::audCommand_Enqueue"
ADDRESS = 0x821AAEE8
SOURCE = "src/rage/audio/rage_audio.cpp"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    count = t.index % 256
    index = rng.randrange(64)
    ring = t.alloc((index + 260) * 4, "commandRing")
    params = t.alloc(max(count, 1) * 4, "parameters") if count else 0
    if count and t.index % 7 == 0:
        params = ring + index * 4 + rng.choice([0, 4, 8])
    if count and t.index % 11 == 0:
        params = 0x825EE220
    t.w32(0x825EE220, index)
    t.w32(0x825EBD2C, ring)
    t.args(r3=rng.getrandbits(32), r4=rng.getrandbits(32),
           r5=params, r6=(rng.getrandbits(24) << 8) | count)
