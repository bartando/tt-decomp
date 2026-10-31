"""0x82483AD8: retain, reload replaced interface and publish four-byte pointer."""
from liftcheck.spec import *
from specs._locked_interface_inputs import inputs as setup, CALLS
FUNCTION = 'CCalMoviePlayer::QueryPhysicsInstance'
ADDRESS = 0x82483AD8
SOURCE = 'src/game/misc/pong_misc.cpp'
TRIALS = 300


def inputs(t):
    obj = setup(t)
    owner = t.alloc(0x70, 'movieAndGuards') + 16
    replacement = t.alloc(16, 'replacementInterface')
    t.w32(obj + 8, owner)
    t.w32(obj + 12, replacement)
    t.w32(owner + 0x38, obj)
    output = t.pick((owner + 0x38, t.alloc(32, 'outputAndGuards') + 12))
    t.args(r3=owner, r4=output)
