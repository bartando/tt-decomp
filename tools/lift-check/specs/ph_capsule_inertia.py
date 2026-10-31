"""0x82411B78: capsule mass/radius/full length, diagonal xyz, r6 output.

Sphere limit (length zero), degenerate/negative geometry, zero/negative mass,
nonfinite values, unrelated r3-r5 and untouched result W/guards. No ignores.
"""
from liftcheck.spec import *
from specs._capsule_inertia_inputs import values
FUNCTION = 'phCapsule_ComputeInertia'
ADDRESS = 0x82411B78
SOURCE = 'src/physics/ph_update_object.cpp'
TRIALS = 600
FTOL = 1e-99
FP_CONTRACT = 'off'


def inputs(t):
    mass, radius, length = values(t)
    output = t.alloc(48, 'inertiaAndGuards', floats=[(16, 3)]) + 16
    t.args(r3=t.rng.getrandbits(32), r4=t.rng.getrandbits(32),
           r5=t.rng.getrandbits(32), r6=output, f1=mass, f2=radius, f3=length)
