from liftcheck.spec import *
from specs.camera_transition_clamp import inputs, transition
FUNCTION = "pongCameraMgr_3650_fw"
ADDRESS = 0x821F3650
SOURCE = "src/game/camera/pong_camera_helpers.cpp"
TRIALS = 512
CALLS = {"pongCameraMgr_6E08": model(transition, args=("r3", "r4", "r5", "r6", "r7"),
                                   deref={"r4": 8, "r6": 8}, preserves=("f11",))}
