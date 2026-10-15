"""gmLogicSwingPractice::ResetTarget (slot 10, 0x82102A58)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmLogicSwingPractice::ResetTarget"
ADDRESS = 0x82102A58
SOURCE = "src/game/match/pong_match.cpp"


def inputs(t):
    rng = t.rng
    logic = t.alloc(0xA0, "logic", ctype="gmLogicSwingPractice")
    t.w32(logic + 0x98, t.alloc(0x70, "target", ctype="gmPracticeTarget"))
    t.w8(logic + 0x9C, rng.choice([0, 1, 0x40]))
    t.args(r3=logic)
