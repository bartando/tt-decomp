"""0x82350808: original coefficient math, padding and alias behavior."""
from liftcheck.spec import *
from specs._spatial_solver_inputs import inverse_regularized as inputs
FUNCTION = 'phMatrix_InvertRegularized'
ADDRESS = 0x82350808
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
FTOL = 1e-99
