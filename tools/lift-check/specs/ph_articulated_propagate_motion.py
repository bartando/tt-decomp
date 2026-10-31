"""0x82258450: child-only joint propagation and post-call velocity caching.

Virtual effects and pointer table replacements distinguish pre/post-call reads.
Arbitrary W, nonpositive counts, duplicate bodies and untouched guards included.
"""
from liftcheck.spec import *
from specs._articulated_joint_inputs import inputs, CALLS

FUNCTION = "phArticulatedCollider_8450"
ADDRESS = 0x82258450
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 400
FP_CONTRACT = "off"
FTOL = 1e-99
