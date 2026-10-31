"""0x82126BD0: clear only ten dynamic-state vectors, retaining intervening data."""
from liftcheck.spec import *

FUNCTION = "phArticulatedBody_ClearState"
ADDRESS = 0x82126BD0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 300


def inputs(t):
    body = t.alloc(0x480, 'bodyAndGuards') + 16
    t.args(r3=body)
