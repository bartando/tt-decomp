"""0x82250818: bone r4, position r5, VMX relative offset and joint-data reload."""
from liftcheck.spec import *
from specs._articulated_response_caller_inputs import inputs as caller_inputs, RESOLVE
from specs.ph_articulated_build_point_response import CALLS as RESPONSE_CALLS
FUNCTION = 'rage::phArticulatedCollider::BuildJointPointResponse'
ADDRESS = 0x82250818
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 200
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = dict(RESPONSE_CALLS, phArticulatedCollider_E668=RESOLVE,
             phArticulatedCollider_BuildPointResponse=run(deref={'r5': 16}))


def inputs(t):
    caller_inputs(t)
