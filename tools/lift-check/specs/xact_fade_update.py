"""Fade state transitions and callbacks at 0x82453B48."""
from liftcheck.spec import *

FUNCTION = "rage::xactFade_Update"
ADDRESS = 0x82453B48
SOURCE = "src/rage/audio/xact_fade.cpp"
TRIALS = 1000
CALLS = {
    "rage::xactFade_ApplyCurve": stub(ret="void", args=("r3",), deref={"r3": 24}),
    "fade.vfn_0": stub(ret="void", args=("r3",), deref={"r3": 24}),
    "fade.vfn_1": stub(ret="void", args=("r3",), deref={"r3": 24}),
}

def inputs(t):
    r = t.rng
    fade = t.alloc(24, "fade")
    t.w32(fade, t.vtable("fade", slots=2))
    t.wf32(fade + 4, r.uniform(-2, 2))
    t.w16(fade + 8, r.choice([0, 1, 2, 5, 10, 100, 65535]))
    t.w32(fade + 12, r.randrange(4))
    t.w32(fade + 16, r.choice([0, 1, 1, 2, 2, 3, 0xffffffff]))
    t.wf32(fade + 20, r.choice([0, 0.5, 1, -1, 2, float("nan"), r.uniform(-1, 2)]))
    t.args(r3=fade)
