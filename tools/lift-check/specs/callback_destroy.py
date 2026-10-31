"""0x821E7BC0 dispatches the first function word directly."""
from liftcheck.spec import *

FUNCTION = "sysCallback_Destroy"
ADDRESS = 0x821E7BC0
SOURCE = "src/anim/anim_blender_state.cpp"
TRIALS = 1000
CALLS = {"cleanup": stub(ret="void", args=("r3",))}


def inputs(t):
    callback = t.alloc(16, "callback")
    t.w32(callback, t.fake_fn("cleanup"))
    t.args(r3=callback)
