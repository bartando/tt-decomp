"""0x820CA488: court-edge braking, signed velocities, and x/z pointer aliasing.

Court bounds and rate are controlled at their boundaries. The rate callback
changes the instance position after the caller must have snapshotted it. Actual
sqrt executes. Compare every call, float, output and guard byte exactly. Finite
nonnegative rates/distances; zero/signed zero/NaN incoming velocities included.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover_AdjustVelocity"
ADDRESS = 0x820CA488
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
EXTERNS = {"g_pInputArrayTable": 0x825EAB28}


def bounds(ctx):
    lo, hi = struct.unpack(">II", ctx.read(ctx.r(3), 8))
    ctx.write(ctx.r(5), ctx.read(lo, 16))
    ctx.write(ctx.r(6), ctx.read(hi, 16))


def rate(ctx):
    mover = ctx.r(3)
    creature = int.from_bytes(ctx.read(mover + 0x70, 4), 'big')
    instance = int.from_bytes(ctx.read(creature + 0xA4, 4), 'big')
    ctx.write(instance + 0x40, struct.pack('>4f', 100., -100., 100., -100.))
    ctx.ret(f1=struct.unpack('>f', ctx.read(mover + 0x4C, 4))[0])


CALLS = {
    0x821C9CD0: model(bounds, args=("r3", "r4", "r5", "r6")),
    0x820CB368: model(rate, args=("r3",)),
    0x824301D0: run(args=("f1",)),
}


def inputs(t):
    rng = t.rng
    mover = t.alloc(0x110, "mover with guards") + 16
    creature = t.alloc(0xD0, "creature")
    instance = t.alloc(0x80, "instance")
    match = t.alloc(0x10, "court model")
    lower, upper = [t.alloc(16, name) for name in ("lower", "upper")]
    for a in (lower, upper, instance + 0x40):
        t.floats(a, 4, -10, 10)
    t.w32(match, lower)
    t.w32(match + 4, upper)
    t.w32(t.sym("g_pInputArrayTable"), match)
    t.w32(mover + 0x70, creature)
    t.w32(creature + 0xA4, instance)
    t.w32(mover + 0x44, rng.getrandbits(32))
    t.wf32(mover + 0x4C, rng.choice((0., 0.5, 2., rng.uniform(0, 20))))
    out = t.alloc(48, "velocities with guards")
    x, z = out + 16, out + (16 if t.index % 5 == 0 else 24)
    velocities = (0., -0., -2., 2., -100., 100., float('nan'), rng.uniform(-50, 50))
    t.wf32(x, velocities[t.index % 8])
    t.wf32(z, rng.choice(velocities))
    if t.index % 9 == 0:
        # Exact stopping limit sqrt(4*2*2) = 4; adjacent values too.
        t.wf32(instance + 0x40, 0.)
        t.wf32(instance + 0x48, 0.)
        for a in (lower, upper):
            t.wf32(a, 4.)
            t.wf32(a + 8, 4.)
        t.wf32(mover + 0x4C, 2.)
        t.wf32(x, rng.choice((-4., 4., -4. - 2**-20, 4. + 2**-20)))
    t.args(r3=mover, r4=x, r5=z)
