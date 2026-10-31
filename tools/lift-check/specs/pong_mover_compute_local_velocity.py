"""0x820CA640: cached velocity, target arrival, target helper and saturation.

The blend callback changes the instance position after it must be copied. The
helper supplies all four output lanes and changes the speed limit. Check all
bytes, including preserved w outside the arrival path and zero w on arrival.
Only three target coordinates are meaningful: its scratch w is uninitialized.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongMover_ComputeLocalVelocity"
ADDRESS = 0x820CA640
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def blend(ctx):
    mover = ctx.r(3)
    creature = int.from_bytes(ctx.read(mover + 0x70, 4), 'big')
    instance = int.from_bytes(ctx.read(creature + 0xA4, 4), 'big')
    ctx.write(instance + 0x40, struct.pack('>4f', 50., 60., 70., 80.))
    ctx.ret(f1=struct.unpack('>f', ctx.read(mover + 0xD0, 4))[0])


def velocity(ctx):
    mover = ctx.r(4)
    ctx.write(ctx.r(3), ctx.read(mover + 0x90, 16))
    ctx.write(mover + 0x48, ctx.read(mover + 0xD4, 4))
    ctx.ret(r3=ctx.r(3))


CALLS = {0x820CB598: model(blend, args=("r3",)),
         0x824301D0: run(args=("f1",)),
         0x820CA9A0: model(velocity, args=("r3", "r4", "r5", "r6"),
                          deref={"r5": 16, "r6": 12})}


def inputs(t):
    rng = t.rng
    mover = t.alloc(0x100, "mover")
    creature = t.alloc(0xD0, "creature")
    instance = t.alloc(0x80, "instance")
    t.w32(mover + 0x70, creature)
    t.w32(creature + 0xA4, instance)
    t.floats(instance + 0x40, 4, -5, 5)
    t.floats(mover + 0x10, 12, -10, 10)
    t.floats(mover + 0x90, 4, -20, 20)
    t.w8(mover + 0x40, rng.randrange(256))
    t.wf32(mover + 0x48, rng.uniform(0, 5))
    t.wf32(mover + 0x50, rng.choice((-1., 0., 10., float('nan'))))
    t.wf32(mover + 0xD0, (0., -1., 0.5, float('nan'))[t.index % 4])
    t.wf32(mover + 0xD4, rng.choice((0., 1., -2., 10., float('nan'))))
    if t.index % 10 == 0:
        t.wf32(instance + 0x40, 0.)
        t.wf32(instance + 0x48, 0.)
        t.wf32(mover + 0x10, 3.)
        t.wf32(mover + 0x14, 4.)
        t.wf32(mover + 0x50, 5.)
        t.wf32(mover + 0xD0, 1.)
    out = t.alloc(48, "output with guards") + 16
    t.args(r3=out, r4=mover)
