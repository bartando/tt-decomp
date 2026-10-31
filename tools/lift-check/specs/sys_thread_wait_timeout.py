"""Nonalertable wait forwards the full timeout and returns the extended result."""
from liftcheck.spec import *
FUNCTION = '_pg_C3B8_g'
ADDRESS = 0x8242C3B8
SOURCE = 'src/xam/thread_sync.cpp'
TRIALS = 1000
CALLS = {'sysThread_WaitTimeoutEx': stub(ret=lambda c: c.rng.getrandbits(32), args=('r3', 'r4', 'r5'))}


def inputs(t):
    t.args(r3=t.alloc(16, 'handle'), r4=t.rng.choice([0, 1, 0xFFFFFFFF, t.u32()]))
