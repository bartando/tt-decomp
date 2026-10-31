"""0x822577F0: solve three unit-force columns in sequence, restoring every selector."""
from liftcheck.spec import *
from specs._articulated_single_response_inputs import inputs as impulse_inputs, CALLS as IMPULSE_CALLS
FUNCTION = 'phArticulatedCollider_BuildPointResponse'
ADDRESS = 0x822577F0
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300
FTOL = 1e-99
FP_CONTRACT = 'off'
# The shared symbol scanner does not parse multidimensional array declarations.
EXTERNS = {'g_phResponseBasis': 0x825CB790}
CALLS = dict(IMPULSE_CALLS, phArticulatedCollider_ApplyPointImpulseResponse=run())


def inputs(t):
    data, array, target, point = impulse_inputs(t)
    t.args(r3=data, r4=target, r5=point)
