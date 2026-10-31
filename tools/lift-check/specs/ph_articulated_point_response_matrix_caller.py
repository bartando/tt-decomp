"""0x822501F8: r4 output, primary/alternate targets and bone indices, live joint data."""
from liftcheck.spec import *
from specs._articulated_response_caller_inputs import inputs as caller_inputs, RESOLVE
from specs.ph_articulated_point_response_matrix import CALLS as MATRIX_CALLS
FUNCTION = 'rage::phArticulatedCollider::GetJointPointResponseMatrix'
ADDRESS = 0x822501F8
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 400
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = dict(MATRIX_CALLS, phArticulatedCollider_E668=RESOLVE,
             phArticulatedCollider_GetPointResponseMatrix=run(deref={'r5': 16}))


def inputs(t):
    point, alternate, bone, alternate_bone = caller_inputs(t)
    output = t.alloc(80, 'matrixAndGuards', floats=[(16, 12)]) + 16
    for row in range(3):
        t.ignore(output + row * 16 + 12, 4)
    t.args(r4=output, r5=point, r6=alternate, r7=bone, r8=alternate_bone)
