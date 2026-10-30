"""0x82152EE0 rebuilds pixel-space scale/translation when window size changes."""
from liftcheck.spec import *

FUNCTION = "grcViewport::UpdateScreenMatrix"
ADDRESS = 0x82152EE0
SOURCE = "src/game/camera/pong_camera.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def inputs(t):
    viewport = t.alloc(0x390, "viewport")
    width = t.pick([1, 3, 719, 1280, -1, -719, 16777217])
    height = t.pick([1, 3, 721, 720, -1, -721, 16777217])
    t.w32(0x825C9014, width)
    t.w32(0x825C9018, height)
    mode = t.pick([0, 1, 2, 3])
    t.w32(viewport + 0x330, width if mode in (0, 1) else width + 1)
    t.w32(viewport + 0x334, height if mode in (0, 2) else height + 1)
    for off in range(0x2C0, 0x300, 4):
        t.wf32(viewport + off, t.f32())
    for off in range(0x300, 0x314, 4):
        t.wf32(viewport + off, t.pick([0.0, 0.5, 1.0, -0.5, t.f32(-2, 2)]))
    t.args(r3=viewport)
