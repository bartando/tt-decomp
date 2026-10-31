"""0x82256B40: restore saved angular/point velocities, recover origin velocity.

Saved/current states differ, arbitrary W is copied bitwise, scalar cross uses
fused subtraction, zero/negative counts and repeated pointers are exercised.
"""
from liftcheck.spec import *
from specs._articulated_step_inputs import bodies

FUNCTION = "phArticulatedCollider_RestoreVelocities"
ADDRESS = 0x82256B40
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
FTOL = 1e-99


def inputs(t):
    data, array = bodies(t)
    if t.index % 5 == 0:
        t.w32(t.rng.choice(array) + t.rng.choice((0xC0, 0x410, 0x420)) + 4 * t.rng.randrange(4),
              t.rng.choice((0, 0x80000000, 1, 0x807FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000)))
    t.args(r3=data)
