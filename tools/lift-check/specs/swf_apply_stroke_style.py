"""Texture unbind before reading style, signed factors/adds, clamp and alpha."""
from liftcheck.spec import *

FUNCTION = "rage::swfApplyStrokeStyle"
ADDRESS = 0x82406290
SOURCE = "src/rage/swf_paint.cpp"
TRIALS = 800


def bind(c):
    # The callback can change the style and transform. Scratch holds the input
    # addresses, so both sides see the same callback effects.
    stroke = int.from_bytes(c.read(0x82606120, 4), "big")
    state = int.from_bytes(c.read(0x82606124, 4), "big")
    c.write(stroke + 4, c.rng.randbytes(4))
    c.write(state + 0x38, c.rng.randbytes(8))
    c.write(state + 0x47, c.rng.randbytes(1))


CALLS = {"bind": model(bind, args=("r3",))}


def inputs(t):
    stroke = t.alloc(8, "stroke")
    state = t.alloc(0x90, "transform")
    t.w32(0x82606120, stroke)
    t.w32(0x82606124, state)
    t.w32(0x82602820, t.fake_fn("bind"))
    t.args(r3=stroke, r4=state)
