"""0x8228E888: transformed AABB union, empty reset, center flag and origin radius."""
from liftcheck.spec import *
from specs._composite_bounds_inputs import inputs, CALLS
FUNCTION = 'rage::phBoundComposite_RebuildExtents'
ADDRESS = 0x8228E888
SOURCE = 'src/physics/composite_bounds.cpp'
TRIALS = 600
FTOL = 1e-99
FP_CONTRACT = 'off'
