"""0x82259108: original coefficient math, padding and alias behavior."""
from liftcheck.spec import *
from specs._spatial_solver_inputs import rotate_diagonal as inputs
FUNCTION = 'phMatrix_RotateDiagonal'
ADDRESS = 0x82259108
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
FTOL = 1e-99
