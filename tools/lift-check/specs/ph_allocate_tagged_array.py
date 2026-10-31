"""0x8256BAF0: wrapped 32-bit product, exact allocation flags and returned pointer."""
from liftcheck.spec import *
FUNCTION = 'rage::phBoundCapsule_AllocArray'
ADDRESS = 0x8256BAF0
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400


def allocate(ctx):
    ctx.ret(r3=0 if ctx.rng.randrange(4) == 0 else ctx.alloc(32))


CALLS = {'rage_AllocInternal': model(allocate, args=('r3', 'r4'))}


def inputs(t):
    values = (0, 1, 3, -1, -3, 0x7fffffff, 0x80000000, 0x40000001, t.u32())
    t.args(r3=t.pick(values), r4=t.pick(values))
