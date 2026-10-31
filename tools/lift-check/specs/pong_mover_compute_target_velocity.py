"""0x820CA9A0: target-speed envelope, VMX normalization, two live speed queries.

Distinct scripted returns and side effects check snapshot ordering. Every lane,
return, call and guard is compared. Finite inputs avoid overflow; zeros and
subnormal source lanes test VMX flushing. The emulator uses a true rsqrt estimate
with the original refinement; hardware's estimate accuracy is a harness limit.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover_ComputeTargetVelocity"
ADDRESS = 0x820CA9A0
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def speed(ctx):
    mover = ctx.r(3)
    n = int.from_bytes(ctx.read(mover + 0xE8, 4), 'big')
    ctx.write(mover + 0xE8, (n + 1).to_bytes(4, 'big'))
    ctx.ret(f1=struct.unpack('>f', ctx.read(mover + 0xD0 + 4 * n, 4))[0])


CALLS = {0x824301D0: run(args=("f1",)),
         0x820CB4D0: model(speed, args=("r3",))}


def inputs(t):
    rng = t.rng
    mover = t.alloc(0x100, "mover")
    t.wf32(mover + 0x18, rng.choice((0., 0.01, 0.5, 2., -1.)))
    t.wf32(mover + 0xD0, rng.choice((0., 1., 100., -2., rng.uniform(-10, 10))))
    t.wf32(mover + 0xD4, rng.choice((0., 5., -3., rng.uniform(-10, 10))))
    t.w32(mover + 0xE8, 0)
    storage = t.alloc(128, "vectors with guards")
    origin, target = storage + 16, storage + 64
    t.floats(origin, 4, -5, 5)
    t.floats(target, 4, -5, 5)
    if t.index % 8 < 3:
        for lane in range(4):
            t.wf32(origin + 4 * lane, 0.)
            t.wf32(target + 4 * lane, 0.)
        t.wf32(target, (0., 0.1, 1.)[t.index % 8])
    if t.index % 8 == 3:
        t.w32(target + 4, rng.choice((1, 0x80000001)))
    out = storage + (16 if t.index % 5 == 0 else 64 if t.index % 5 == 1 else 96)
    t.args(r3=out, r4=mover, r5=origin, r6=target)
