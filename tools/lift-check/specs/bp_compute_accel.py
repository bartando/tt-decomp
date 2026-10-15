"""ballPredict::ComputeAccel (0x822832D0): the predictor's flight model,
0.004 * (spin x vel) - c * |vel| * vel + (0, -9.8, 0) * gravityScale."""
import math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "ballPredict::ComputeAccel"
ADDRESS = 0x822832D0
SOURCE = "src/game/ball/ball_predict.cpp"
EXTERNS = {"crt_sqrt": 0x824301D0, "crt_tan": 0x82432628, "g_ppBallInst": 0x8271A2F4}
FTOL = 1e-5     # clang fuses the multiply-adds the vector code rounds twice


def _tan(ctx):
    ctx.ret(f1=math.tan(ctx.f(1)))


CALLS = {
    0x824301D0: run(),
    0x82432628: model(_tan),
    "phys.vfn_12": stub(ret=lambda ctx: ctx.ret(f1=ctx.rng.uniform(0.0, 2.0))),
}


def inputs(t):
    rng = t.rng
    out = t.alloc(16, "out", ctype="bpVec4")
    params = t.alloc(0xD0, "params")
    t.w32(params + 0xCC, rng.choice([0, 8, 9, 10, 10]))
    vel = t.alloc(16, "vel")
    scale = rng.choice([1e-4, 1.0, 10.0])
    t.floats(vel, 4, -scale, scale)
    if rng.random() < 0.15:
        t.wf32(vel, 0.0)
    spin = t.alloc(16, "spin")
    t.floats(spin, 4, -300.0, 300.0)
    phys = t.alloc(16, "phys")
    t.w32(phys, t.vtable("phys", 16))
    inst = t.alloc(16, "inst")
    t.w32(inst + 4, phys)
    cell = t.alloc(4, "cell")
    t.w32(cell, inst)
    t.w32(0x8271A2F4, cell)
    t.args(r3=out, r4=params, r5=vel, r6=spin)
