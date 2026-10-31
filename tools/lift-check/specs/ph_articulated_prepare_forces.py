"""0x82255FE0: resolved responses -> cached and current origin velocities.

Execute original tree response and spatial multiply, with modeled real virtuals.
All memory/calls compare; dependency lifts are verified separately.
"""
from liftcheck.spec import *
from specs._articulated_force_inputs import CALLS as TREE_CALLS, inputs
FUNCTION = 'phArticulatedCollider_5FE0'
ADDRESS = 0x82255FE0
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FP_CONTRACT = 'off'
FTOL = 1e-99
CALLS = dict(TREE_CALLS, phArticulatedCollider_PrepareForceResponse=run())
