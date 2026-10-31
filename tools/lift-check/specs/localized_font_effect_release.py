"""32-bit reference wrapping, destroy-on-zero, and stable zero return after delete."""
from liftcheck.spec import *

FUNCTION = "localizedFontEffectRelease"
ADDRESS = 0x82151268
SOURCE = "src/rage/localized_font_effect.cpp"
TRIALS = 500


def destroy(c):
    c.write(c.r(3) + 0x20, b"\xa5\x5a\x12\x34")
    c.ret(r3=0x12345678)


CALLS = {0x821512B8: model(destroy, args=("r3", "r4"))}


def inputs(t):
    effect = t.alloc(0x24, "effect")
    t.w32(effect + 0x20, t.rng.choice((0, 1, 1, 2, 0x7fffffff, 0xffffffff, t.rng.getrandbits(32))))
    t.args(r3=effect)
