"""0x822A2F28: base property copy, five vectors, parameter tail and reset refcount."""
from liftcheck.spec import *
from specs._bound_copy_inputs import inputs, CALLS
FUNCTION = 'rage::phBoundCapsule::CopyFrom'
ADDRESS = 0x822A2F28
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 600
FTOL = 1e-99
