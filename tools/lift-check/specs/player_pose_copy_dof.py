"""0x82378450: invoke the channel's real slot-six CopyFrom operation."""
from liftcheck.spec import *

FUNCTION = "playerPose_CopyDof"
ADDRESS = 0x82378450
SOURCE = "src/game/player/player_auxiliary_animation_helpers.cpp"
TRIALS = 1000
CALLS = {"target.vfn_6": stub(ret="void", args=("r3", "r4"))}


def inputs(t):
    dst = t.alloc(0x20, "destination")
    t.w32(dst, t.vtable("target"))
    t.args(r3=dst, r4=t.alloc(0x20, "source"), f1=t.rng.uniform(-5, 5),
           r5=t.rng.getrandbits(32), r6=t.rng.getrandbits(32))
