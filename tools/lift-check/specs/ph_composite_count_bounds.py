"""0x8228E750: count all direct slots and nested descendants, including nulls."""
from liftcheck.spec import *
from specs._composite_bound_inputs import tree

FUNCTION = "rage::phBoundComposite_E750"
ADDRESS = 0x8228E750
SOURCE = "src/physics/bound_lookup.cpp"
TRIALS = 400


def inputs(t):
    bound, _ = tree(t)
    t.args(r3=bound)
