"""0x82460850: shared critical section, virtual AddRef and saved return value."""
from liftcheck.spec import *
from specs._locked_interface_inputs import inputs, CALLS
FUNCTION = 'phObject_AddRefLocked'
ADDRESS = 0x82460850
SOURCE = 'src/physics/locked_interface.cpp'
TRIALS = 400
