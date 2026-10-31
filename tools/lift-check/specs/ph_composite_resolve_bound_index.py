"""0x8228F5C8: map flattened descendant indices to immediate composite children."""
from liftcheck.spec import *
from specs._composite_bound_inputs import index_inputs as inputs

FUNCTION = "rage::phBoundComposite_ResolveBoundIndex"
ADDRESS = 0x8228F5C8
SOURCE = "src/physics/bound_lookup.cpp"
TRIALS = 400
CALLS = {"rage::phBoundComposite_E750": run()}
