"""gmPracticeTarget::AddToDrawBucket (slot 2, 0x82113448)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmPracticeTarget::AddToDrawBucket"
ADDRESS = 0x82113448
SOURCE = "src/game/match/pong_match.cpp"

EXTERNS = {"g_drawBucket": 0x826064F4, "pongDrawBucket_AddEntry": 0x822278D8}
CALLS = {0x822278D8: stub(ret="void")}


def inputs(t):
    rng = t.rng
    target = t.alloc(0x70, "target", ctype="gmPracticeTarget")
    t.w8(target + 0x14, rng.choice([0, 1, 0x80]))
    t.w8(target + 0x15, rng.choice([0, 1, 0x80]))
    t.w32(0x826064F4, t.alloc(0x40, "drawBucket"))
    t.args(r3=target)
