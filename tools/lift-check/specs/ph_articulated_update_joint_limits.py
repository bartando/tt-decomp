"""0x82250528: five typed output arrays, dirty flag, count return stored at +1D8."""
from liftcheck.spec import *
from specs._articulated_limit_inputs import inputs as limit_inputs, CALLS as LIMIT_CALLS
FUNCTION = 'rage::phArticulatedCollider::UpdateJointConstraintErrors'
ADDRESS = 0x82250528
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = dict(LIMIT_CALLS, phArticulatedCollider_GatherJointLimits=run())


def inputs(t):
    data, arrays = limit_inputs(t)
    collider = t.alloc(0x250, 'colliderAndGuards')
    t.w32(collider + 0x1D0, data)
    for offset, address in zip((0x1DC, 0x1E4, 0x1EC, 0x1F4, 0x1FC), arrays):
        t.w32(collider + offset, address)
    t.args(r3=collider)
