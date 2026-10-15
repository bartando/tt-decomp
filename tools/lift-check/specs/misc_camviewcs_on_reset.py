"""camViewCS::OnReset (slot 8): resets both sources through slot 8, clears state."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "camViewCS::OnReset"
ADDRESS = 0x8216CE40
SOURCE = "src/game/camera/pong_camera.cpp"


def inputs(t):
    rng = t.rng
    view = t.alloc(0x48, "camViewCS", ctype="camViewCS")
    src = t.alloc(0xB0, "source")
    t.w32(src, t.vtable("source"))
    other = 0
    if rng.random() < 0.7:
        other = t.alloc(0xB0, "other")
        t.w32(other, t.vtable("other"))
    t.w32(view + 0x2C, src)
    t.w32(view + 0x34, other)
    t.wf32(view + 0x14, rng.uniform(-5, 5))
    t.args(r3=view)
