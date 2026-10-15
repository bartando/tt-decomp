"""CheckButtonPressed (0x821DFFF8): bit 7 of now/previous against the released byte."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "CheckButtonPressed"
ADDRESS = 0x821DFFF8
SOURCE = "src/game/input/button_edges.cpp"


def inputs(t):
    rec = t.alloc(4, "record")
    t.args(r3=rec)
