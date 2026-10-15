"""grcViewport::SetCameraMtx: stores the camera matrix, its w-forced copy, the
inverse (0x820D50A0, stubbed: it fills the stack matrix with random floats on
both sides) w-forced, and that with z negated; then calls 0x82153070."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "grcViewport::SetCameraMtx"
ADDRESS = 0x821539F0
SOURCE = "src/game/camera/pong_camera.cpp"
FTOL = 0


def inputs(t):
    vp = t.alloc(0x390, "viewport", ctype="grcViewport")
    for off in (0x40, 0x180, 0x1C0, 0x200):
        t.floats(vp + off, 16, -50, 50)
    mtx = t.alloc(0x40, "cameraMtx", ctype="CamMatrix44")
    t.floats(mtx, 16, -50, 50)
    t.args(r3=vp, r4=mtx)
