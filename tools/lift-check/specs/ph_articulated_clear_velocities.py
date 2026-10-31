"""0x82255A40: clear eight body vectors and dispatch child joint slot 17."""
from liftcheck.spec import *
from specs._articulated_joint_inputs import inputs, CALLS

FUNCTION = "phArticulatedCollider_ResetForceAccumulators"
ADDRESS = 0x82255A40
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 400
