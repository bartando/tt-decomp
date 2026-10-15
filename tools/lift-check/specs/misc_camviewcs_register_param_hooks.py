"""camViewCS::RegisterParamHooks (slot 3): three param-hook registrations."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "camViewCS::RegisterParamHooks"
ADDRESS = 0x8216CEB0
SOURCE = "src/game/camera/pong_camera.cpp"
EXTERNS = {"pongCameraView_RegisterParamHook": 0x82177B60}

CALLS = {
    0x82177B60: stub(ret="void", args=("r3", "r4", "r5", "r6", "r7", "r8")),
}


def inputs(t):
    view = t.alloc(0x48, "camViewCS")
    host = t.alloc(0x40, "paramHost")
    t.args(r3=view, r4=host)
