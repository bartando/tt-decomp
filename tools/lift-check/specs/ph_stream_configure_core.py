"""0x824662F8: configuration arguments, guards and HRESULT propagation."""
from liftcheck.spec import *
from specs._stream_configuration_inputs import inputs as setup, CALLS
FUNCTION = 'phStream_Configure'
ADDRESS = 0x824662F8
SOURCE = 'src/physics/stream_configuration.cpp'
TRIALS = 400


def inputs(t):
    obj = setup(t)
    t.args(r3=obj + (0))
