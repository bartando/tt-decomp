"""0x82258e48: original coefficient math, padding and alias behavior."""
from liftcheck.spec import *
from specs._spatial_solver_inputs import body_inertia as inputs
FUNCTION = 'phArticulatedBody_BuildInertia'
ADDRESS = 0x82258e48
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
FTOL = 1e-99
CALLS = {"phMatrix_RotateDiagonal": run()}
