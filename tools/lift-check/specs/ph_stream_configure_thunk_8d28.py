"""0x82468D28: packed format width/channel reload and returned status."""
from liftcheck.spec import *
from specs._stream_configuration_inputs import inputs as setup, CALLS
FUNCTION = 'rage::ph_vt5B98_12_Thunk'
ADDRESS = 0x82468D28
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300


def inputs(t):
    obj = setup(t)
    t.w8(obj + 0xb0, t.pick((0, 1, 2)))
    t.w8(obj + 0xb1, t.rng.randrange(256))
    t.w8(obj + 0xfc, 1)
    t.w8(obj + 0xfd, t.pick((0, 1, 2)))
    t.w8(obj + 0xfe, t.rng.randrange(256))
    t.args(r3=obj + (0))
