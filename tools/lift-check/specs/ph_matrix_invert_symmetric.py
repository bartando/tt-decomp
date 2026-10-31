"""0x8225b7e0: original coefficient math, padding and alias behavior."""
from liftcheck.spec import *
from specs._spatial_solver_inputs import inverse_symmetric as inputs
FUNCTION = 'phMatrix_InvertSymmetric'
ADDRESS = 0x8225b7e0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
FTOL = 1e-99
