"""0x820D0658: orthonormal basis extraction, exact scalar rounding and xyz stores."""
from liftcheck.spec import *
from specs._mat33_euler_inputs import inputs, CALLS
FUNCTION = 'rage::mat33ToEulerZXY'
ADDRESS = 0x820D0658
SOURCE = 'src/rage/math/mat33_extract_euler.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
