"""Drain a non-cyclic font list using the original release helper, including refs>1."""
from liftcheck.spec import *
from specs._localized_font_lifecycle_inputs import RELEASE_CALLS

FUNCTION = "localizedFontShutdown"
ADDRESS = 0x8240A208
SOURCE = "src/rage/localized_font_lifecycle.cpp"
TRIALS = 300
CALLS = {**RELEASE_CALLS, 0x82409278: run()}


def inputs(t):
    head = 0
    for _ in range(t.rng.randrange(7)):
        font = t.alloc(0x17C, "font")
        t.w32(font + 0x174, head)
        t.w32(font + 0x178, t.rng.choice((1, 2, 3)))
        head = font
    t.w32(0x826066E0, head)
