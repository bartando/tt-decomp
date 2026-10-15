"""camViewCS::OnSourceChanged (slot 9): the source's slot 9, then clears
m_viewFlags unless the viewed source is m_otherSource."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "camViewCS::OnSourceChanged"
ADDRESS = 0x8216CD30
SOURCE = "src/game/camera/pong_camera.cpp"


def inputs(t):
    rng = t.rng
    view = t.alloc(0x48, "camViewCS")
    src = t.alloc(0xB0, "source")
    t.w32(src, t.vtable("source"))
    t.w32(view + 0x2C, src)
    t.w32(view + 0x34, src if rng.random() < 0.5 else rng.getrandbits(32))
    t.args(r3=view)
