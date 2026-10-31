"""First allocation only, 16-bit count/capacity stores and full-width overflow."""
from liftcheck.spec import *

FUNCTION = "localizedFontResizeArray"
ADDRESS = 0x8240A250
SOURCE = "src/rage/localized_font_array.cpp"
TRIALS = 600
_data = 0
CALLS = {0x820DEC88: model(lambda c: c.ret(r3=_data), args=("r3",))}


def inputs(t):
    global _data
    rng = t.rng
    array = t.alloc(8, "array")
    t.w32(array, t.alloc(16, "previousData"))
    t.w16(array + 6, rng.choice((0, 0, 1, 2, 0xffff)))
    _data = t.alloc(16, "allocatedData") if rng.randrange(2) else 0
    t.args(r3=array, r4=rng.choice((0, 1, 2, 65535, 65536, 65537,
                                    0x3fffffff, 0x40000000, 0xffffffff, rng.getrandbits(32))))
