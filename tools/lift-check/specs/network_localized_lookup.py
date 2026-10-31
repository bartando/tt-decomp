"""0x82408F08: bucket lookup, missing-table failure and cached fallback entries."""
from liftcheck.spec import *
from specs._network_localized_globals import EXTERNS
FUNCTION = "localizedTextLookup"
ADDRESS = 0x82408F08
SOURCE = "src/rage/data/localized_text.cpp"
TRIALS = 400
CALLS = {0x82569394: run(transparent=True, args=()), "localizedTextHash": run(), "localizedWideDuplicate": run(),
         "localizedWideLength": run(), "localizedTextInsert": run(),
         "rage_Alloc": alloc(), "localizedFontCreate": stub(ret=0x45000000, args=('r3',)),
         "nop_8240E6D0": stub(ret='void', args=('r3',))}

def _hash(data):
    value = 0
    for c in data:
        value = (value * 16 + (c if c < 128 else c - 256)) & 0xFFFFFFFF
        high = value & 0xF0000000
        if high: value ^= high ^ (high >> 24)
    return value

def inputs(t):
    table = t.alloc(12, 'table')
    n = t.rng.choice([1,2,3,7,16])
    buckets = t.alloc(n * 4, 'buckets', fill='zero')
    t.w32(table, n)
    t.w32(table + 4, buckets)
    t.w32(table + 8, t.rng.choice([0,1,0xFFFFFFFF,t.u32()]))
    key_bytes = bytes(t.rng.randrange(1,256) for _ in range(t.rng.choice([0,1,3,16,64])))
    key = t.alloc(len(key_bytes) + 1,'key',fill=key_bytes + b'\0')
    target = _hash(key_bytes)
    for i in range(n):
        previous = buckets + i * 4
        for j in range(t.rng.randrange(4)):
            node = t.alloc(12, 'node')
            t.w32(previous, node)
            t.w32(node, target if t.rng.random() < 0.25 else t.u32())
            value = t.alloc(24, 'text value') if t.rng.random() < 0.8 else 0
            t.w32(node + 4, value)
            previous = node + 8
        t.w32(previous, 0)
    t.w32(t.sym('g_localizationTable'), 0 if t.index % 11 == 0 else table)
    t.w32(t.sym('g_localizationDefaultFontName'), t.rng.choice([0,t.alloc(8, 'font name', fill=b'Arial\0')]))
    t.args(r3=t.sym('g_localizationTable'), r4=key)
