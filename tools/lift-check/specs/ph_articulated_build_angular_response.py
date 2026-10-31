"""0x82257918: solve three unit-torque columns and restore every selector."""
from liftcheck.spec import *
from specs._articulated_single_response_inputs import inputs
from specs._articulated_single_response_inputs import CALLS as IMPULSE_CALLS
FUNCTION = 'phArticulatedCollider_BuildAngularResponse'
ADDRESS = 0x82257918
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300
FTOL = 1e-99
FP_CONTRACT = 'off'
# The shared symbol scanner does not parse multidimensional array declarations.
EXTERNS = {'g_phResponseBasis': 0x825CB790}
CALLS = dict(IMPULSE_CALLS, phArticulatedCollider_ApplyAngularImpulseResponse=run())
