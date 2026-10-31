"""0x8223BE20: three-argument relative transform and the two vector rotations.

The unlifted 0x8223BBB0 boundary records full quaternion/vector inputs and fills
all four output lanes deterministically. Conjugate multiplication executes its
original body on both sides and has its own C++ differential spec. No excluded
memory. Shared/overlapping transforms exercise the original store sequence.
"""
from liftcheck.spec import *
FUNCTION = 'LocomotionStateAnim_BE20_g'
ADDRESS = 0x8223BE20
SOURCE = 'src/rage/math/quat_ops.cpp'
TRIALS = 600
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = {'util_BBB0': stub(ret='void', args=('r3','r4','r5'),
                         deref={'r3': 16, 'r4': 16}, out={'r5': 16}),
         'rage::quatMultiplyConjugate': run()}


def inputs(t):
    block = t.alloc(0x140, 'relativeTransformsAndGuards', floats=[(0, 0x140 // 4)])
    t.floats(block, 0x140 // 4, -4, 4)
    left = block + 0x50
    right = t.pick((left, left - 0x10, left + 0x10, block + 0xb0))
    output = t.pick((left, right, left - 0x10, left + 0x10, block + 0xe0))
    t.args(r3=output, r4=left, r5=right)
