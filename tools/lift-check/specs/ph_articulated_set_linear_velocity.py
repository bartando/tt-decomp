"""0x82258A30: root-relative velocity shift and angular/point velocity caches.

Checks all four lanes, xyz cross product, nonpositive/multiple body counts,
input aliases, repeated body pointers, subnormals and nonfinite inputs.
No ignored bytes; finite float32 values must match exactly. VMX flush follows lift-check's model.
"""
from liftcheck.spec import *
from specs._articulated_velocity_inputs import velocity_inputs as inputs

FUNCTION = "phArticulatedCollider_8A30"
ADDRESS = 0x82258A30
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"

# Below float32 resolution: only NaN encodings and signed zero may differ.
FTOL = 1e-99
