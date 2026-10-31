"""Unsigned milliseconds to relative 100ns units; infinite does not write storage."""
FUNCTION = 'sysThread_MillisecondsTimeout'
ADDRESS = 0x8242C390
SOURCE = 'src/xam/thread_sync.cpp'
TRIALS = 1200


def inputs(t):
    storage = t.alloc(32, 'timeoutAndGuards') + 8
    t.args(r3=storage, r4=t.rng.choice([0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFE, 0xFFFFFFFF, t.u32()]))
