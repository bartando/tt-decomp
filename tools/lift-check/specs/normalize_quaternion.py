"""Four-lane normalization, including zero, tiny and large magnitudes."""
from liftcheck.spec import *

FUNCTION = "rage::(anonymous namespace)::NormalizeQuaternion(float*)"
ADDRESS = 0x820C42D8
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
RET = None


def inputs(t):
    r = t.rng
    quat = t.alloc(16, "quat")
    mode = r.randrange(6)
    for i in range(4):
        value = (0.0 if mode == 0 else r.choice((0.0, -0.0)) if mode == 1
                 else r.uniform(-1e-20, 1e-20) if mode == 2
                 else r.uniform(-1e-30, 1e-30) if mode == 3
                 else r.uniform(-1e19, 1e19) if mode == 4
                 else r.uniform(-100, 100))
        t.wf32(quat + i * 4, value)
    t.args(r3=quat)
