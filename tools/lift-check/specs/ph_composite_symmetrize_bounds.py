"""0x8228F3E0: select farthest signed side, half diagonal, clear full centroid.

Preserve upper/lower W lanes and centroid-present byte, including its nonzero
values. Equal magnitudes and NaNs select the upper side. The common Newton
refinement and mutable sentinel are checked with zero/tiny/infinite widths.
"""
from liftcheck.spec import *
FUNCTION = 'rage::phBoundComposite_Symmetrize'
ADDRESS = 0x8228F3E0
SOURCE = 'src/physics/composite_bounds.cpp'
TRIALS = 800
FTOL = 1e-99
FP_CONTRACT = 'off'


def inputs(t):
    obj = t.alloc(0x90, 'symmetricBoundAndGuards', floats=[(16, 20)]) + 16
    t.floats(obj + 8, 18, -10, 10)
    pairs = ((0., -0.), (-0., 0.), (1., -1.), (1., 1.), (-1., -1.),
             (2., -1.), (-2., 1.), (.5, -3.), (-.5, 3.),
             (1e-40, -1e-40), (float('inf'), 1.), (1., float('inf')),
             (float('nan'), 1.), (1., float('nan')))
    for axis in range(3):
        upper, lower = pairs[(t.index + axis) % len(pairs)] if t.index % 3 else (t.rng.uniform(-10,10), t.rng.uniform(-10,10))
        t.wf32(obj + 0x10 + axis * 4, upper)
        t.wf32(obj + 0x20 + axis * 4, lower)
    t.w8(obj + 5, t.pick((0, 1, 2, 0x80, 0xff)))
    t.wf32(t.sym('lbl_82619BF0'), t.pick((0., float('inf'))))
    t.args(r3=obj)
