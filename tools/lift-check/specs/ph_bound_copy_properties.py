"""0x8228DA50: preserve vtable, copy each vector before its store and 14 trailing bytes."""
from liftcheck.spec import *
from specs._bound_copy_inputs import inputs, CALLS
FUNCTION = 'rage::phBound_CopyProperties'
ADDRESS = 0x8228DA50
SOURCE = 'src/physics/bound_copy.cpp'
TRIALS = 600
FTOL = 1e-99
