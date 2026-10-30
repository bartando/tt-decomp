"""Two distinct or shared matrices, including inputs already in the viewport."""
from liftcheck.spec import *

FUNCTION = "grcViewport::SetTransformMatrices"
ADDRESS = 0x821538C0
SOURCE = "src/game/camera/pong_camera.cpp"
TRIALS = 1000
FTOL = 0
CALLS = {"game_3070": stub(ret="void", args=("r3",), deref={"r3": 256})}


def inputs(t):
    vp = t.alloc(0x390, "viewport", ctype="grcViewport")
    first = t.alloc(0x40, "first", ctype="CamMatrix44")
    second = t.alloc(0x40, "second", ctype="CamMatrix44")
    t.floats(vp, 64, -100, 100)
    t.floats(first, 16, -100, 100)
    t.floats(second, 16, -100, 100)
    first = t.rng.choice([first, vp, vp + 0x40])
    second = t.rng.choice([second, first, vp, vp + 0x40, vp + 0x80, vp + 0xc0])
    t.args(r3=vp, r4=first, r5=second)
