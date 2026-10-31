"""0x8224F040: complete original articulated timestep pipeline through all stages.

Run original force, limit, integration, restore, propagation, rebase and rebuild
routines; dependencies also have individual lift checks. Child joint virtuals
are deterministic models. Ignore only the inverse's undefined C padding row.
"""
from liftcheck.spec import *
from specs._articulated_force_inputs import CALLS as FORCE_CALLS
from specs.ph_articulated_rebuild_solver import CALLS as SOLVER_CALLS, inputs as setup
FUNCTION = 'rage::phArticulatedCollider::SetTimestep'
ADDRESS = 0x8224F040
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 96
FP_CONTRACT = 'off'
FTOL = 1e-99
CALLS = dict(FORCE_CALLS, **SOLVER_CALLS)
CALLS.update({name: run() for name in (
    'phArticulatedCollider_5FE0', 'phArticulatedCollider_PrepareForceResponse',
    'phArticulatedCollider_60F8', 'rage::ph_IntegrateJointPositions',
    'phArticulatedCollider_BuildRotation', 'crt_sqrt', 'crt_sin', 'crt_cos',
    'phArticulatedCollider_RestoreVelocities', 'phArticulatedCollider_8450',
    'phArticulatedCollider_F0E0', 'phArticulatedCollider_5D58')})
for i in range(8):
    CALLS[f'forceJoint{i}.vfn_0'] = stub(ret='void')


def inputs(t):
    setup(t)
    data = t.reg_args['r3']
    collider = t.alloc(0x480, 'colliderAndGuards') + 16
    t.floats(collider, 0x460 // 4, -10, 10)
    t.w32(collider + 0x1D0, data)
    t.args(r3=collider, f1=t.rng.choice((1/60, 1/30, 0.005, 0.1)))
