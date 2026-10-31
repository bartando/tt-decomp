"""0x82250870: bone resolution and live joint-data receiver for angular columns."""
from liftcheck.spec import *
from specs._articulated_response_caller_inputs import inputs as caller_inputs, RESOLVE
from specs.ph_articulated_build_angular_response import CALLS as RESPONSE_CALLS
FUNCTION = 'rage::phArticulatedCollider::BuildJointAngularResponse'
ADDRESS = 0x82250870
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 200
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = dict(RESPONSE_CALLS, phArticulatedCollider_E668=RESOLVE,
             phArticulatedCollider_BuildAngularResponse=run())


def inputs(t):
    caller_inputs(t)
