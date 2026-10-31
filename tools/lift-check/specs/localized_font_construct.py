"""Font defaults, untouched glyph/padding bytes, list insertion, registry dedup."""
from liftcheck.spec import *

FUNCTION = "localizedFontConstruct"
ADDRESS = 0x82409338
SOURCE = "src/rage/localized_font_lifecycle.cpp"
TRIALS = 500


def inputs(t):
    font = t.alloc(0x17C, "font")
    head = t.alloc(0x17C, "previousFont") if t.index % 4 == 3 else 0
    t.w32(0x826066E0, head)
    count = t.rng.randrange(1, 6)
    entries = t.alloc(16 * (count + 1), "shutdownRecords")
    for i in range(count):
        t.w32(entries + i * 16, t.alloc(4, "callbackObject"))
        t.w32(entries + i * 16 + 4, t.fake_fn("otherCallback"))
    if t.index % 4 in (1, 2):
        index = t.rng.randrange(count)
        t.w32(entries + index * 16 + 4, 0x8240A208)
        if t.index % 4 == 1:
            t.w32(entries + index * 16, 0)
    if t.index % 7 == 0:
        count = 0
    t.w32(0x825CB9A0, entries)
    t.w16(0x825CB9A4, count)
    t.w16(0x825CB9A6, count + 1)
    t.args(r3=font)
