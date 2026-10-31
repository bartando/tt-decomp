"""0x820d4f88: original coefficient math, padding and alias behavior."""
from liftcheck.spec import *
from specs._spatial_solver_inputs import multiply as inputs
FUNCTION = 'phMatrix_Multiply3x3'
ADDRESS = 0x820d4f88
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
FTOL = 1e-99
