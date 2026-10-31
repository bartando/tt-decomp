"""0x8225DD70: 16 blocks, 20 ctors per block, correct stride/callback and flags."""
from liftcheck.spec import *
FUNCTION = 'phJointChain_Constructor'
ADDRESS = 0x8225DD70
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 40
CALLS = {'phJoint3Dof_0170_g': run(), 'atSingleton_E3F0_p44': run()}


def inputs(t):
    t.args(r3=t.alloc(0xBCB0, 'jointChainAndGuards') + 16)
