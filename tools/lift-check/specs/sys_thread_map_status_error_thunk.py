"""The former fatal-exit thunk delegates to error mapping and returns its value."""
from liftcheck.spec import *
FUNCTION = 'sysThread_SetErrorFromStatusThunk'
ADDRESS = 0x8242BF10
SOURCE = 'src/xam/thread_sync.cpp'
TRIALS = 1000
CALLS = {'sysThread_SetErrorFromStatus': stub(ret=lambda c: c.rng.getrandbits(32), args=('r3',))}


def inputs(t):
    t.args(r3=t.u32())
