"""0x82258FC0: threshold, normalized axis, two four-lane transposes and rotation.

Execute retail sqrt, sin/cos and both existing matrix lifts. All bytes compare;
only equivalent NaNs and signed zeros are permitted by the float comparator.
Reciprocal estimate uses the checker's true reciprocal, not console estimate bits.
"""
from liftcheck.spec import *
from specs._articulated_rotation_inputs import vector
FUNCTION = 'phArticulatedBody_Rotate'
ADDRESS = 0x82258FC0
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 600
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = {'crt_sqrt': run(), 'rage::mat33RotationNormalizedAxis': run(),
         'rage::mat33ComposeInPlace': run(), 'crt_cos': run(), 'crt_sin': run()}


def inputs(t):
    body = t.alloc(0x480, 'bodyAndGuards') + 16
    t.floats(body, 0x460 // 4, -10, 10)
    t.args(r3=body, r4=vector(t, body))
