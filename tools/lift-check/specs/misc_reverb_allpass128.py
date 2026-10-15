"""ReverbAllpass<128>::ProcessInPlace (XAudio reverb, 0x824623E0): the
half-block allpass, two loops. writePos 0 as 0x824631B8 keeps it (the second
loop assumes it)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "ReverbAllpass<128u>::ProcessInPlace(float*)"
ADDRESS = 0x824623E0
SOURCE = "src/physics/ph_physics.cpp"


def inputs(t):
    rng = t.rng
    st = t.alloc(0x218, "allpass")
    t.w32(st + 0x00, rng.randrange(1, 128))
    t.wf32(st + 0x04, rng.uniform(-0.9, 0.9))
    t.wf32(st + 0x08, rng.uniform(-0.9, 0.9))
    t.wf32(st + 0x0C, rng.uniform(-1, 1))
    t.w32(st + 0x10, 0)
    t.floats(st + 0x18, 128, -1, 1)
    buf = t.alloc(4 * 257, "samples")
    t.floats(buf, 257, -1, 1)
    t.args(r3=st, r4=buf)
