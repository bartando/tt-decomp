"""0x82143E98 operates on grcViewport, not pongCameraMgr."""
from liftcheck.spec import *

FUNCTION = "grcViewport::GetAspectRatio"
ADDRESS = 0x82143E98
SOURCE = "src/game/camera/pong_camera.cpp"
TRIALS = 1000
# Each multiply rounds before the divide.
FP_CONTRACT = "off"


def inputs(t):
    viewport = t.alloc(0x390, "viewport")
    t.wf32(viewport + 0x33C, t.pick([0.0, -0.0, 1.0, 1.7777778, -2.0, t.f32(-4, 4)]))
    t.wf32(viewport + 0x320, t.f32(-2, 2))
    t.wf32(viewport + 0x324, t.pick([0.0, -0.0, 0.5, 1.0, -2.0, t.f32(0.1, 3)]))
    for off in (0x330, 0x334):
        t.w32(viewport + off, t.pick([1, -1, 720, 1280, 16777217, -16777217, 2147483647, -2147483648]))
    t.args(r3=viewport)
