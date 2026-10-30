"""Viewport sphere classification: outside / crossing / inside.

Runs the original transform (mat44TransformPoint) and sqrt. Matrices are near-orthonormal
(scale exactly 1, inside and just outside the +-1e-5 window) or random; spheres
land inside, on and outside each plane, with special values in a few slots.
vmsum4fp128 is the emulator's model (double accumulation, one rounding).
"""
from liftcheck.spec import *

FUNCTION = "grcViewport_ClassifySphere"
ADDRESS = 0x82153D18
SOURCE = "src/graphics/grc_viewport_cull.cpp"
FP_CONTRACT = "off"
CALLS = {0x8214EA10: run(), "crt_sqrt": run()}

SPECIAL = [0, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC00000]


def inputs(t):
    rng = t.rng
    vp = t.alloc(0x400, "viewport", fill="zero")
    scale = rng.choice([1.0, 1.0, 0.999995, 1.000004, 0.9999, 1.0002, rng.uniform(0.2, 3)])
    for row in range(4):
        for col in range(4):
            value = (scale if row == col else 0.0) if row < 3 else 0.0
            if rng.random() < 0.3:
                value += rng.uniform(-0.2, 0.2)
            t.wf32(vp + 0x100 + 16 * row + 4 * col, value)
    t.wf32(vp + 0x100 + 48 + 4 * 3, 1.0)
    near, far = rng.uniform(0.1, 5), rng.uniform(20, 200)
    t.wf32(vp + 0x340, near)
    t.wf32(vp + 0x344, far)
    for k in range(8):
        t.wf32(vp + 0x364 + 4 * k, rng.uniform(-1, 1))
    sphere = t.alloc(16, "sphere")
    t.wf32(sphere, rng.uniform(-60, 60))
    t.wf32(sphere + 4, rng.uniform(-60, 60))
    t.wf32(sphere + 8, -rng.choice([near, far, rng.uniform(-10, far + 10)]))
    t.wf32(sphere + 12, rng.choice([0.0, rng.uniform(0, 5), rng.uniform(0, 80)]))
    if rng.random() < 0.1:
        t.w32(sphere + 4 * rng.randrange(4), rng.choice(SPECIAL))
    if rng.random() < 0.05:
        t.w32(vp + 0x340 + 4 * rng.randrange(2), rng.choice(SPECIAL))
    t.args(r3=vp, r4=sphere)
