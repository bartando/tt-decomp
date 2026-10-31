"""0x82257368: pure torque, selected tensor output and bidirectional joint propagation."""
from liftcheck.spec import *
from specs._articulated_single_response_inputs import inputs, CALLS
FUNCTION = 'phArticulatedCollider_ApplyAngularImpulseResponse'
ADDRESS = 0x82257368
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
