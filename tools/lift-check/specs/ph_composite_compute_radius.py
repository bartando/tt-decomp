"""0x8228ECB0: transformed part centers, refined length and reverse-order maximum."""
from liftcheck.spec import *
from specs._composite_bounds_inputs import inputs, CALLS
FUNCTION = 'rage::phBoundComposite_ComputeRadius'
ADDRESS = 0x8228ECB0
SOURCE = 'src/physics/composite_bounds.cpp'
TRIALS = 600
FTOL = 1e-99
FP_CONTRACT = 'off'
