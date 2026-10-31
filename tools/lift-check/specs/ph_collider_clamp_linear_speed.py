"""0x822CAE18: collider clamp linear speed; all memory and W lanes checked."""
from liftcheck.spec import *
from specs._collider_velocity_inputs import inputs, CALLS
FUNCTION = 'phCollider_ClampLinearSpeed'
ADDRESS = 0x822CAE18
SOURCE = 'src/physics/collider_velocity.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
EXTERNS = {'g_floatOne': 0x8202D108, 'g_floatZero': 0x8202D110}
