from liftcheck.spec import *
from specs._cr_anim_dof_copy_inputs import PAYLOADS

FUNCTION = "rage::crAnimDofQuaternion::SetValue"
ADDRESS = 0x820C52D8
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1000
RET = None


def inputs(t):
    obj = t.alloc(64, "dof")
    payload = t.alloc(16, "payload")
    source = t.rng.choice((payload, obj + 8, obj + 16, obj + 24))
    words = t.rng.choice(PAYLOADS) if t.rng.randrange(2) else tuple(t.u32() for _ in range(4))
    for i, word in enumerate(words):
        t.w32(source + 4 * i, word)
    t.args(r3=obj, r4=source)
