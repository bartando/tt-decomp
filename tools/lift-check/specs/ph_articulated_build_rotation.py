"""0x82256D98: solver Rodrigues matrix, scalar rounding and untouched padding."""
from liftcheck.spec import *
FUNCTION = 'phArticulatedCollider_BuildRotation'
ADDRESS = 0x82256D98
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 600
FP_CONTRACT = 'off'
CALLS = {'crt_cos': run(), 'crt_sin': run()}


def inputs(t):
    out = t.alloc(96, 'rotationAndGuards') + 16
    axis = t.alloc(32, 'axisAndGuards')
    if t.index % 3 == 0:
        axis = out + t.rng.choice((0, 16, 32))
    t.floats(axis, 4, -3, 3)
    angle = t.rng.choice((0., 1., -1., 3.141592653589793, t.rng.uniform(-10, 10)))
    t.args(r3=t.rng.getrandbits(32), r4=out, r5=axis, f1=angle)
