"""Aligned objects with guards, identity and forward/backward record overlap."""
from liftcheck.spec import *
CALLS = {'rage::phBound_CopyProperties': run()}


def inputs(t):
    block = t.alloc(0x380, 'boundCopyAndGuards')
    source = block + 0x140
    destination = source + t.pick((-0x100, -0x70, -0x40, -0x20, -0x10, 0, 0x10, 0x20, 0x40, 0x70, 0x100))
    t.float_words.update((source + 8, source + 12, destination + 8, destination + 12))
    t.args(r3=destination, r4=source)
