"""0x821E6470: bpShot assignment copies the payload while preserving padding."""
from liftcheck.spec import *

FUNCTION = "ballPredict_CopyShot"
ADDRESS = 0x821E6470
SOURCE = "src/game/ball/ball_process_hit.cpp"
TRIALS = 400


def inputs(t):
    dst = t.alloc(0xC0, "destination", ctype="bpShot")
    src = dst if t.rng.random() < 0.2 else t.alloc(0xC0, "source", ctype="bpShot")
    t.args(r3=dst, r4=src)
