"""0x82468D00: current record field and HRESULT forwarding."""
from liftcheck.spec import *
from specs._stream_record_inputs import inputs as setup, CALLS
FUNCTION = 'rage::ph_vt5A60_24_Thunk'
ADDRESS = 0x82468D00
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300


def inputs(t):
    owner = setup(t)
    t.args(r3=owner + 16)
