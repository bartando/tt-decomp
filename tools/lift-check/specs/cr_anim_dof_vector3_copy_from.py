"""0x820C4850 (72B), vfn_6: exact four-lane copy via source slot 14.

Despite the blend-family vtable position, there is no FP arithmetic, FMA,
normalization or weight test here. Copy all float bit patterns unchanged,
including signed zeros, signaling/quiet NaNs and subnormals; f1 is ignored.
The callback returns a valid aligned 16-byte vector, disjoint or exactly aliased
with this+16. Callback implementation and FP status/traps are outside scope.
"""
from specs._cr_anim_dof_copy_inputs import calls, inputs as copy_inputs

FUNCTION = "rage::crAnimDofVector3::CopyFrom"
ADDRESS = 0x820C4850
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 2000
FTOL = 0
RET = None
CALLS = calls(14)


def inputs(t):
    copy_inputs(t)
