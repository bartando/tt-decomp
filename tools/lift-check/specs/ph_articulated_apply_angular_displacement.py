"""0x82256C28: per-body rotation, position cross term and point-velocity correction.

Run every retail dependency, checking full body/input/guard memory and call order.
Covers signed counts, repeated bodies, vector aliases, threshold and nonfinite cases.
"""
from liftcheck.spec import *
from specs._articulated_rotation_inputs import inputs
from specs.ph_articulated_body_rotate import CALLS as ROTATION_CALLS
FUNCTION = 'phArticulatedCollider_ApplyAngularDisplacement'
ADDRESS = 0x82256C28
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = dict(ROTATION_CALLS, phArticulatedBody_Rotate=run())
