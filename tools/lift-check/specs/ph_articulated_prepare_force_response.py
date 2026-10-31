"""0x82256300: body force transform, reverse reduction, forward propagation."""
from liftcheck.spec import *
from specs._articulated_force_inputs import CALLS, inputs
FUNCTION = 'phArticulatedCollider_PrepareForceResponse'
ADDRESS = 0x82256300
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FP_CONTRACT = 'off'
FTOL = 1e-99
