"""gmLogicSwingPractice::AddToDrawBuckets (slot 15, 0x82102BC0)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gmLogicSwingPractice::AddToDrawBuckets"
ADDRESS = 0x82102BC0
SOURCE = "src/game/match/pong_match.cpp"

CALLS = {"target.vfn_2": stub(ret="void", args=("r3",))}


def inputs(t):
    rng = t.rng
    logic = t.alloc(0xA0, "logic", ctype="gmLogicSwingPractice")
    t.w8(logic + 0x58, rng.choice([0, 1, 0x80]))
    if rng.random() < 0.8:
        target = t.alloc(0x70, "target")
        t.w32(target, t.vtable("target"))
        t.w32(logic + 0x98, target)
    else:
        t.w32(logic + 0x98, 0)
    t.args(r3=logic)
