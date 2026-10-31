"""0x8228CEE0: uint16 bound references, no reset when delete flag is clear."""
from liftcheck.spec import *
from specs._physics_reference_inputs import inputs, CALLS
FUNCTION = 'ph_CEE0'
ADDRESS = 0x8228CEE0
SOURCE = 'src/physics/archetype_refs.cpp'
TRIALS = 400
