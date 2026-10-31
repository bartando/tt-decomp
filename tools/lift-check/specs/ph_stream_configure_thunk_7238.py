"""0x82467238: configuration arguments, guards and HRESULT propagation."""
from liftcheck.spec import *
from specs._stream_configuration_inputs import inputs as setup, CALLS
FUNCTION = 'rage::ph_vt5A60_32_Thunk'
ADDRESS = 0x82467238
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 200


def inputs(t):
    obj = setup(t)
    t.args(r3=obj + (0))
