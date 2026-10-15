"""ReverbTapDelay3<512>::Process (XAudio reverb, 0x82462310): 3-tap delay line,
256 samples; writePos a multiple of 256 as the caller keeps it."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "ReverbTapDelay3<512u>::Process(float const*, float*, float*, unsigned int)"
ADDRESS = 0x82462310
SOURCE = "src/physics/ph_physics.cpp"


def inputs(t):
    rng = t.rng
    st = t.alloc(0x82C, "tapdelay")
    for k in range(3):
        t.w32(st + 12 * k, rng.randrange(0, 512))
        t.wf32(st + 12 * k + 4, rng.uniform(-1, 1))
        t.wf32(st + 12 * k + 8, rng.uniform(-1, 1))
    t.w32(st + 0x24, rng.choice([0, 256]))
    t.floats(st + 0x2C, 512, -1, 1)
    src = t.alloc(4 * 256, "in")
    t.floats(src, 256, -1, 1)
    a = t.alloc(4 * 257, "outA")
    b = t.alloc(4 * 257, "outB")
    t.args(r3=st, r4=src, r5=a, r6=b, r7=256)
