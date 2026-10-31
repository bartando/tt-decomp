"""0x821D61A8: camera/travel-relative spin octant, including unordered axes."""
from liftcheck.spec import *

FUNCTION = "pongBall_ClassifySpin"
ADDRESS = 0x821D61A8
SOURCE = "src/game/ball/ball_shot.cpp"
TRIALS = 1400
EXTERNS = {"g_pCameraSharedState": 0x8271A32C}


def inputs(t):
    rng = t.rng
    spin = t.alloc(16, "spin", floats=[(0, 4)])
    velocity = t.alloc(16, "velocity", floats=[(0, 4)])
    values = [0.0, -0.0, -1.0, 1.0, -3.5, 7.0, float("nan"),
              float("inf"), -float("inf"), 1e-40, -1e-40]
    for lane in range(4):
        t.wf32(spin + lane * 4, rng.choice(values))
        t.wf32(velocity + lane * 4, rng.choice(values))
    camera = t.alloc(16, "camera")
    t.w8(camera + 5, rng.choice([0, 1, 2, 0x80, 0xff]))
    t.w32(0x8271A32C, camera)
    t.args(r3=spin, r4=velocity)
