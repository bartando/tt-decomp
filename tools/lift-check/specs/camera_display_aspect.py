"""Four fixed modes and fallback, including zero dimensions and FP edges."""
from liftcheck.spec import *
FUNCTION = "gameLoop_GetDisplayAspect"
ADDRESS = 0x82228EA0
SOURCE = "src/game/camera/camera_transition_queries.cpp"
TRIALS = 512

def inputs(t):
    state = t.alloc(0x210, "game loop", fill="zero")
    modes = [0, 1, 2, 3, -1, 4, 0x7FFFFFFF, 0x80000000]
    scales = [0., -0., 1., -1., 0.5, 2., float("nan"), float("inf"), -float("inf")]
    t.w32(state + 0x200, modes[t.index % len(modes)])
    t.wf32(state + 0x204, scales[(t.index // len(modes)) % len(scales)]
           if t.index < len(scales) * len(modes) else t.rng.uniform(-100, 100))
    t.w32(0x825C9014, [0, 1, -1, 1280, 0x7FFFFFFF, 0x80000000][(t.index // len(modes)) % 6])
    t.args(r3=state)
