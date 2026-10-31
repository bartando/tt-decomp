"""0x82258C98: flatten constraint virtuals into five arrays, preserving sign-bit clamp.

Includes signed/zero counts, NaN/zero signs, aliased outputs, pointer replacement,
count mutation and the owner-index store observed by each state virtual. No ignores.
"""
from liftcheck.spec import *
from specs._articulated_limit_inputs import inputs, CALLS
FUNCTION = 'phArticulatedCollider_GatherJointLimits'
ADDRESS = 0x82258C98
SOURCE = 'src/physics/articulated_constraints.cpp'
TRIALS = 600
FTOL = 1e-99
FP_CONTRACT = 'off'
