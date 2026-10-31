"""All XOR byte values, including endpoints and arbitrary history bytes."""
from liftcheck.spec import *

FUNCTION = "pongPad_DecodeAxis"
ADDRESS = 0x821E00D8
SOURCE = "src/game/input/analog_axis.cpp"
TRIALS = 512
FP_CONTRACT = "off"


def inputs(t):
    button = t.alloc(4, "button")
    polarity = t.rng.randrange(256)
    t.w8(button, (t.index % 256) ^ polarity)
    t.w8(button + 3, polarity)
    t.args(r3=button)
