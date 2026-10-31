"""0x8223B9A8: scalar fused products and W-before-XYZ alias sequencing."""
from liftcheck.spec import *
FUNCTION = 'rage::quatMultiplyConjugate'
ADDRESS = 0x8223B9A8
SOURCE = 'src/rage/math/quat_ops.cpp'
TRIALS = 1000
FTOL = 1e-99
FP_CONTRACT = 'off'


def inputs(t):
    block = t.alloc(128, 'quaternionInputsAndGuards', floats=[(0, 32)])
    t.floats(block, 32, -8, 8)
    left = block + 32
    right = t.pick((block + 80, left, left + 4, left + 8, left + 12))
    output = t.pick((left, right, left - 4, left + 4, right - 4, right + 4, block + 16))
    if t.index % 7 == 0:
        t.wf32(t.pick((left, right)) + 4 * t.rng.randrange(4),
               t.pick((0., -0., 1e-40, float('nan'), float('inf'), -float('inf'))))
    t.args(r3=output, r4=left, r5=right)
