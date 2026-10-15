"""charViewCS::RegisterAxisHooks (slot 3, 0x8216DBB8, camBaseCS's own slot 3): registers
camBaseCS's six tunables, BlendTime/BlendGoal/CameraFOV/Near/Far (+0x9C..+0xAC, kind 6)
and IgnoreTimeWarp (+0xB4, kind 1)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "charViewCS::RegisterAxisHooks"
ADDRESS = 0x8216DBB8
SOURCE = "src/game/camera/pong_camera.cpp"

CALLS = {
    0x82177B60: stub(ret="void", args=("r3", "r4", "r5", "r6", "r7", "r8")),
}


def inputs(t):
    cs = t.alloc(0x130, "charViewCS")
    host = t.alloc(0x40, "paramHost")
    t.args(r3=cs, r4=host)
