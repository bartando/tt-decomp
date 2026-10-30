"""Rebuild an SWF affine transform from rotation, residual, scale and translation.

Limits: valid aligned 0x90-byte state only. Rotation builder and concat run as
original code on both sides; sin/cos are libm boundary models, not CRT tests.
No float tolerance or ignored memory; this does not measure native performance.
"""
import math
from liftcheck.spec import *

FUNCTION = "rage::swfRebuildTransform"
ADDRESS = 0x823FB018
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
RET = None
CALLS = {
    0x823FA2A0: run(),
    0x824302B0: model(lambda c: c.ret(f1=math.cos(c.f(1))) if math.isfinite(c.f(1)) else c.ret(f1=float('nan')), args=("f1",)),
    0x824301D8: model(lambda c: c.ret(f1=math.sin(c.f(1))) if math.isfinite(c.f(1)) else c.ret(f1=float('nan')), args=("f1",)),
    0x823FA1E0: run(),
}
CALLS[0x823FA1E0].deref = {"r4": 24, "r5": 24}


def inputs(t):
    rng = t.rng
    state = t.alloc(0x90, "transform")
    t.floats(state, 35, -200, 200)
    special = (0, 0x80000000, 0x42c80000, 0x3f800000, 0xbf800000,
               0x7f800000, 0xff800000, 0x7fc00000, 1, 0x7f7fffff)
    for i in range(35):
        if rng.random() < 0.12:
            t.w32(state + i * 4, rng.choice(special))
    if rng.randrange(3) == 0:
        t.w32(state + 0x4c, rng.choice((0, 0x80000000)))
    mode = rng.randrange(4)
    if mode == 0:
        t.wf32(state + 0x60, 100.0)
        t.wf32(state + 0x64, 100.0)
    elif mode == 1:
        t.wf32(state + 0x60, 100.0)
    elif mode == 2:
        t.wf32(state + 0x64, 100.0)
    if rng.randrange(4) == 0:
        t.wf32(0x825C8078, rng.choice((0.0, -0.0, 0.005, 0.1)))
    t.args(r3=state)
