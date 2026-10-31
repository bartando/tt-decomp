"""0x82255558: original coefficient math, padding and alias behavior."""
from liftcheck.spec import *
from specs._spatial_solver_inputs import tensor_pair as inputs
FUNCTION = 'phSpatialTensor_Difference'
ADDRESS = 0x82255558
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 600
FP_CONTRACT = "off"
FTOL = 1e-99
