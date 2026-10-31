"""Semaphore release forwards previous-count pointer and maps negative statuses."""
from liftcheck.spec import *
FUNCTION = '_pg_6DC0_g'
ADDRESS = 0x82566DC0
SOURCE = 'src/xam/thread_sync.cpp'
TRIALS = 1200
CALLS = {
    'NtReleaseSemaphore': stub(ret=lambda c: c.rng.choice([0, 1, 0x7FFFFFFF, 0x80000000, 0xC000000D]),
                              args=('r3', 'r4', 'r5')),
    'sysThread_SetErrorFromStatusThunk': stub(ret=5, args=('r3',)),
}


def inputs(t):
    t.args(r3=t.alloc(16, 'semaphore'), r4=t.rng.choice([-1, 0, 1, 2, 100]),
           r5=t.alloc(4, 'previousCount') if t.index % 2 else 0)
