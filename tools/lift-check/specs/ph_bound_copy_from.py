"""0x8228DA18: shared property copy followed by a uint16 reference reset."""
from liftcheck.spec import *
from specs._bound_copy_inputs import inputs, CALLS
FUNCTION = 'rage::phBound::CopyFrom'
ADDRESS = 0x8228DA18
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FTOL = 1e-99
