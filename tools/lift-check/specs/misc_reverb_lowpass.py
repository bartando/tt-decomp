"""ReverbLowPass::Process (XAudio reverb, 0x824621E0): two one-pole low-passes
over sampleCount samples. The binary forms (x*gain)*(1-c) for three of every
four samples where the lift forms x*(gain*(1-c)), hence FTOL (reverb-poc saw
1.2e-7)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "ReverbLowPass::Process"
ADDRESS = 0x824621E0
SOURCE = "src/physics/ph_physics.cpp"
FTOL = 1e-6


def inputs(t):
    rng = t.rng
    n = rng.choice([0, 1, 3, 4, 7, 256])
    st = t.alloc(0x20, "lowpass", ctype="ReverbLowPass")
    t.floats(st + 0x10, 2, -1, 1)
    t.wf32(st + 0x18, rng.uniform(0.1, 2.0))
    t.wf32(st + 0x1C, rng.uniform(0.0, 0.99))
    src = t.alloc(4 * max(n, 1), "in")
    t.floats(src, n, -1, 1)
    out = t.alloc(4 * (n + 1), "out")
    t.floats(out, n + 1, -1, 1)
    t.args(r3=st, r4=src, r5=out, r6=n)
