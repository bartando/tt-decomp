"""0x82228990: localization lookup, BMP UTF-8, clipping and control replacement."""
from liftcheck.spec import *
from specs._network_localized_globals import EXTERNS
FUNCTION = "rage_atStringCopy"
ADDRESS = 0x82228990
SOURCE = "src/rage/data/localized_text.cpp"
TRIALS = 600
CALLS = {0x82434520: MODELS["memcpy"], "localizedTextLookup": stub(ret=0x45000000, args=('r3','r4'))}
def inputs(t):
    entry = t.map(0x45000000, 0x1000, 'entry')
    wide = t.alloc(130, 'UTF-16')
    for i in range(64):
        t.w16(wide + i * 2, t.rng.choice([1, 10, 0x1C, 0x1D, 127, 128, 2047, 2048, 0xD800, 0xFFFF, t.rng.randrange(1, 65536)]))
    t.w16(wide + t.rng.randrange(65) * 2, 0)
    t.w32(entry + 8, wide)
    destination = t.alloc(200, 'UTF-8 output')
    key = t.alloc(16, 'key', fill=b'KEY\0')
    t.args(r3=key, r4=destination, r5=t.rng.choice([0,1,2,3,4,5,16,64,192]))
