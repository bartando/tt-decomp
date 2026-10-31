"""0x821DC4F8: four 544-byte blocks, retail nop ctor, 3-record resets.

Run original iterator and reset. Ignore only reset's undefined per-record W.
"""
from liftcheck.spec import *
FUNCTION = 'rage::phJoint3Dof_C4F8_w'
ADDRESS = 0x821DC4F8
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 200
CALLS = {'phJoint3Dof_0170_g': run(), 'nop_8240E6D0': run(), 'util_4628': run()}


def inputs(t):
    obj = t.alloc(0x8A0, 'fourBlocksAndGuards') + 16
    for block in range(4):
        for record in range(3):
            for offset in (12, 28, 44):
                t.ignore(obj + block * 544 + record * 64 + offset, 4)
    t.args(r3=obj)
