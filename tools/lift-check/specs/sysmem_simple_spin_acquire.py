"""Uncontended lock acquisition and non-1 lock values that return unchanged.

A lock value of 1 spins until another thread changes it; this single-threaded
checker cannot exercise that transition or contention and reservation failures.
"""
from liftcheck.spec import *

FUNCTION = "sysMemSimpleAllocator_SpinAcquire"
ADDRESS = 0x82187D90
SOURCE = "src/rage/memory/sysMemSimpleAllocator.cpp"
TRIALS = 1000


def inputs(t):
    lock = t.alloc(12, "lock_and_guards")
    value = t.rng.choice((0, 0, 2, 3, 0x80000000, 0xFFFFFFFF, t.u32() | 2))
    t.w32(lock + 4, value)
    t.args(r3=lock + 4)
