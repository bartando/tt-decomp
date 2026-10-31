"""0x82255f10: original coefficient math, padding and alias behavior."""
from liftcheck.spec import *
from specs._spatial_solver_inputs import tensor_pair as inputs
FUNCTION = 'phSpatialTensor_Copy'
ADDRESS = 0x82255f10
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 400
FP_CONTRACT = "off"
FTOL = 1e-99
