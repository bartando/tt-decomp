"""0x822571C8: force/point cross term, selected tensor output, ancestor path and branches."""
from liftcheck.spec import *
from specs._articulated_single_response_inputs import inputs, CALLS
FUNCTION = 'phArticulatedCollider_ApplyPointImpulseResponse'
ADDRESS = 0x822571C8
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
