"""0x824668D8: current record field and HRESULT forwarding."""
from liftcheck.spec import *
from specs._stream_record_inputs import inputs as setup, CALLS
FUNCTION = 'phStream_GetRecordField'
ADDRESS = 0x824668D8
SOURCE = 'src/physics/stream_configuration.cpp'
TRIALS = 300


def inputs(t):
    owner = setup(t)
    t.args(r3=owner + 0)
