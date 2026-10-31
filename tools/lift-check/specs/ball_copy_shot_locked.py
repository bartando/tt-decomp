"""0x82287040: publish the complete shot and preserve disabled-lock diagnostics."""
from liftcheck.spec import *
FUNCTION = "CopyVectorThreadSafe"
ADDRESS = 0x82287040
SOURCE = "src/game/ball/ball_process_hit.cpp"
TRIALS = 400
CALLS = {"ballPredict_CopyShot": run(),
         "nop_8240E6D0": stub(ret="void", args=("r3",), deref={"r3": 37})}

def inputs(t):
    context = t.alloc(0x1A0, "context")
    shot = context + 0x40 if t.index % 5 == 0 else t.alloc(0xC0, "shot", ctype="bpShot")
    t.w8(context + 0x105, t.rng.choice([0, 1, 2, 255]))
    t.args(r3=context, r4=shot)
