from liftcheck.spec import *
from specs.camera_transition_mode6 import inputs as base_inputs, transition
FUNCTION = "pongCameraMgr_3500_fw"
ADDRESS = 0x821F3500
SOURCE = "src/game/camera/pong_camera_helpers.cpp"
TRIALS = 512
CALLS = {"pongCameraMgr_6E08": model(transition, args=("r3", "r4", "r5", "r6", "r7"),
                                   deref={"r4": 8}, preserves=("f11",))}

def inputs(t):
    base_inputs(t)
    t.args(r5=t.rng.choice([0, 1, 3, 6, -1, 0x7FFFFFFF]))
