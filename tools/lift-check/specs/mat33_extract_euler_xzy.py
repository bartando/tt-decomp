"""0x82234360: private orthonormal basis, XZY extraction and preserved output W."""
from liftcheck.spec import *
from specs._mat33_euler_inputs import inputs, CALLS
FUNCTION = 'rage::mat33ToEulerXZY'
ADDRESS = 0x82234360
SOURCE = 'src/rage/math/mat33_extract_euler.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
