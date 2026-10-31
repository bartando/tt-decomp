"""0x8225b498: original coefficient math, padding and alias behavior."""
from liftcheck.spec import *
from specs._spatial_solver_inputs import invert_tensor as inputs
FUNCTION = 'phSpatialTensor_Invert'
ADDRESS = 0x8225b498
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 400
FP_CONTRACT = "off"
FTOL = 1e-99
CALLS = {"phMatrix_InvertSymmetric": run(), "phMatrix_Multiply3x3": run(),
         "rage::mat33ComposeInPlace": run(), "phMatrix_InvertRegularized": run()}
