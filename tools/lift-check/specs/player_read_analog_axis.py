"""Pad remapping, exhaustive byte axis values, dead zone and float return ABI."""
from liftcheck.spec import *

FUNCTION = "pongPlayer_0508_g"
ADDRESS = 0x821E0508
SOURCE = "src/game/input/analog_axis.cpp"
TRIALS = 1024
FP_CONTRACT = "off"
CALLS = {0x821E0270: run(), 0x821E00D8: run()}


def inputs(t):
    pad = t.alloc(0x328, "pad")
    for k in range(4, 8):
        t.w8(pad + k, t.rng.choice([0, 1, 255]))
    buttons = t.alloc(0x100, "buttons")
    t.w32(pad + 0x31C, buttons)
    # Fill every possible remapped slot with the same XOR so all 256 axis
    # values run through each flag combination over the trial set.
    for k in range(64):
        polarity = t.rng.randrange(256)
        t.w8(buttons + k * 4, (t.index % 256) ^ polarity)
        t.w8(buttons + k * 4 + 3, polarity)
    t.args(r3=pad, r4=t.rng.randrange(0x3A), f1=t.rng.uniform(-20, 20))
