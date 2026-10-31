"""0x82258B10: angular delta, position cross correction, and refreshed caches.

Same adversarial body layout as the linear setter. In particular W participates
in the VMX cross correction, while scalar cached-point cross writes only xyz.
"""
from liftcheck.spec import *
from specs._articulated_velocity_inputs import velocity_inputs as inputs

FUNCTION = "phArticulatedCollider_8B10"
ADDRESS = 0x82258B10
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"

# Below float32 resolution: only NaN encodings and signed zero may differ.
FTOL = 1e-99
