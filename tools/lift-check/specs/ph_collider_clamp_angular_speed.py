"""0x822CAEA8: collider clamp angular speed; all memory and W lanes checked."""
from liftcheck.spec import *
from specs._collider_velocity_inputs import inputs, CALLS
FUNCTION = 'phCollider_ClampAngularSpeed'
ADDRESS = 0x822CAEA8
SOURCE = 'src/physics/collider_velocity.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
EXTERNS = {'g_floatOne': 0x8202D108, 'g_floatZero': 0x8202D110}
