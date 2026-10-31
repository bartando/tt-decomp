"""0x822557F0: dynamic clear, saved-pose restore, caches and two flag arrays.

Run the original single-body helper; separately verify its lifted implementation.
Includes nonpositive/multiple counts, duplicate bodies, arbitrary W/nonfinites.
"""
from liftcheck.spec import *
from specs._articulated_step_inputs import bodies

FUNCTION = "phArticulatedCollider_ResetJointChain"
ADDRESS = 0x822557F0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
FTOL = 1e-99
CALLS = {"phArticulatedBody_ClearState": run()}


def inputs(t):
    data, array = bodies(t)
    if t.index % 5 == 0:
        t.w32(t.rng.choice(array) + 0x100 + 4 * t.rng.randrange(4),
              t.rng.choice((1, 0x807FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000)))
    t.args(r3=data)
