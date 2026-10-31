import math
from liftcheck.spec import *

CALLS = {0x821AAEE8: stub(ret="void", args=("r3", "r4", "r5", "r6"), deref={"r5": 8})}

def voice(t):
    owner = t.alloc(64, "voiceAndGuards") + 16
    ref = t.alloc(32, "sfxReference")
    t.w32(owner + 12, ref)
    return owner

def values(t):
    return t.rng.choice([0., -0., 1., -1., -2., 3., 4., 0.5, -0.5,
                         math.inf, -math.inf, math.nan,
                         t.rng.uniform(-100, 100), 2.**-140,
                         2.**32, -2.**32, 2.**63])
