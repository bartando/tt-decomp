"""0x8224FD50: preserve rotation vector r4 when loading joint-data receiver."""
from liftcheck.spec import *
from specs._articulated_rotation_inputs import inputs as joint_inputs
from specs.ph_articulated_apply_angular_displacement import CALLS as MOTION_CALLS
FUNCTION = 'rage::phArticulatedCollider::ApplyAngularDisplacement'
ADDRESS = 0x8224FD50
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 200
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = dict(MOTION_CALLS, phArticulatedCollider_ApplyAngularDisplacement=run())


def inputs(t):
    data, rotation = joint_inputs(t)
    collider = t.alloc(0x250, 'colliderAndGuards')
    t.w32(collider + 0x1D0, data)
    t.args(r3=collider, r4=rotation)
