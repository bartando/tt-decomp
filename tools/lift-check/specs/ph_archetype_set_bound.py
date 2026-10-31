"""0x822C9E50: retain the incoming bound before releasing the old, including aliases."""
from liftcheck.spec import *
from specs._physics_reference_inputs import swap_inputs as inputs, CALLS
FUNCTION = 'ph_9E50'
ADDRESS = 0x822C9E50
SOURCE = 'src/physics/archetype_refs.cpp'
TRIALS = 400
