"""0x822CC700: preserve r4 and forward the embedded displacement vector."""
from liftcheck.spec import *
from liftcheck.machine import ARENA_BASE
from specs.ph_vector_accumulate_projected import inputs as setup
FUNCTION = 'rage::phArticulatedCollider::DelegateToBoundCapsule'
ADDRESS = 0x822CC700
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = {'phVector_AccumulateProjected': run()}


def inputs(t):
    setup(t)
    vector = t.reg_args['r3']
    obj = t.alloc(0x200, 'colliderAndGuards') + 16
    t.put(obj + 0x160, bytes(t.arena[vector - ARENA_BASE:vector - ARENA_BASE + 16]))
    t.float_words.update(obj + 0x160 + i * 4 for i in range(4))
    if t.reg_args['r4'] == vector:
        t.args(r4=obj + 0x160)
    t.args(r3=obj)
