"""CMtoCSAdapter::PublishCameraMatrix: five named-value lookups (cmNamedValueSet
slot 1, each returns a fresh 16-byte block) and a row copied into each."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "CMtoCSAdapter::PublishCameraMatrix"
ADDRESS = 0x821722F8
SOURCE = "src/game/camera/pong_camera.cpp"

CALLS = {
    "values.vfn_1": alloc(size_reg=None, size=16, args=("r3", "r4")),
}


def inputs(t):
    adapter = t.alloc(0x140, "adapter")
    cam = t.alloc(0x20, "cmCamera")
    values = t.alloc(0x10, "values")
    t.w32(values, t.vtable("values"))
    t.w32(cam + 0x18, values)
    t.w32(adapter + 0x130, cam)
    mtx = t.alloc(0x40, "cameraMtx", ctype="CamMatrix44")
    t.floats(mtx, 16, -50, 50)
    t.args(r3=adapter, r4=mtx)
