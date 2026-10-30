"""CheckButtonPressed (0x821DFFF8): bit 7 of now/previous against the released byte."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "CheckButtonPressed"
ADDRESS = 0x821DFFF8
SOURCE = "src/game/input/button_edges.cpp"
TRIALS = 1000


def inputs(t):
    rec = t.alloc(4, "record")
    # Exercise every combination of current, previous and released high bits.
    bits = t.index % 8
    for offset, shift in ((0, 0), (1, 1), (3, 2)):
        t.w8(rec + offset, (t.u32() & 0x7f) | (((bits >> shift) & 1) << 7))
    t.args(r3=rec)
