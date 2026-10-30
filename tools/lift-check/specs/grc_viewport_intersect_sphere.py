"""Viewport sphere intersection and optional view-space depth.

Tests identity and perturbed transforms, each side and depth boundary, null and
non-null output, and unordered comparisons. Float inputs are single precision;
this does not cover non-float values passed in FPRs by non-C++ callers.
"""
from liftcheck.spec import *

FUNCTION = "grcViewport_IntersectSphere"
ADDRESS = 0x82153BF8
SOURCE = "src/graphics/grc_viewport_cull.cpp"
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    vp = t.alloc(0x400, "viewport", fill="zero")
    # The four side planes are +/-x and +/-y, with a z component.
    for row in range(4):
        for col in range(3):
            value = 1.0 if row == col else 0.0
            if rng.random() < 0.2:
                value += rng.uniform(-1, 1)
            t.wf32(vp + 0x200 + row * 16 + col * 4, value)
    for i, value in enumerate([1, -0.5, -1, -0.5, 1, -0.5, -1, -0.5]):
        t.wf32(vp + 0x364 + 4 * i, value)
    t.wf32(vp + 0x340, 1.0)
    t.wf32(vp + 0x344, 20.0)
    x, y, z = (rng.uniform(-15, 15), rng.uniform(-15, 15), rng.uniform(-5, 25))
    radius = rng.choice([0.0, 1.0, rng.uniform(0, 10)])
    # Force exact boundaries and just-outside cases with an identity transform.
    if rng.random() < 0.5:
        for row in range(4):
            for col in range(3):
                t.wf32(vp + 0x200 + row * 16 + col * 4, float(row == col))
        z = rng.choice([0.0, 1.0, 10.0, 20.0, 21.0])
        x = y = 0.0
        axis = rng.randrange(6)
        delta = rng.choice([0.0, -0.001, 0.001])
        if axis < 4:
            v = 0.5 * z + radius + delta
            if axis == 0: x = v
            if axis == 1: x = -v
            if axis == 2: y = v
            if axis == 3: y = -v
        elif axis == 4:
            z = 1.0 - radius + delta
        else:
            z = 20.0 + radius + delta
    # This case puts the first side plane one ULP below the fused x transform.
    # It distinguishes both fused operations from separately rounded products.
    if rng.random() < 0.1:
        for row in range(4):
            for col in range(3):
                t.wf32(vp + 0x200 + row * 16 + col * 4, 0.0)
        for i in range(8):
            t.wf32(vp + 0x364 + 4 * i, 0.0)
        t.wf32(vp + 0x200, 0.16158433258533478)
        t.wf32(vp + 0x210, 1.7628834247589111)
        t.wf32(vp + 0x220, 2.529729127883911)
        t.wf32(vp + 0x37C, 0.0)
        t.wf32(vp + 0x36C, 1.0)
        t.wf32(vp + 0x340, -100.0)
        t.wf32(vp + 0x344, 100.0)
        x, y, z, radius = 2.7423365116119385, 0.8694329261779785, 2.3295047283172607, 7.868843078613281
    if rng.random() < 0.04:
        t.w32(vp + rng.choice([0x200, 0x238, 0x364, 0x340, 0x344]), 0x7FC00000)
    out = t.alloc(4, "view_z") if rng.random() < 0.7 else 0
    t.args(r3=vp, f1=x, f2=y, f3=z, f4=radius, r8=out)
