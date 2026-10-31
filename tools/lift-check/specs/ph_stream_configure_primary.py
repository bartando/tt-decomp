"""0x82466A50: configuration arguments, guards and HRESULT propagation."""
from liftcheck.spec import *
from specs._stream_configuration_inputs import inputs as setup, CALLS
FUNCTION = 'phStream_ConfigurePrimary'
ADDRESS = 0x82466A50
SOURCE = 'src/physics/stream_configuration.cpp'
TRIALS = 400


def inputs(t):
    obj = setup(t)
    t.args(r3=obj + (-16))
