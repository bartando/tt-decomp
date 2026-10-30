"""0x820C4D30 (80B), vfn_6: exact ordered 64-bit copies via source slot 15.

No FMA, interpolation, hemisphere flip, normalization or weight test occurs.
All float bit patterns (including NaN payloads/signaling bits, signed zeros and
subnormals) compare byte-exactly. f1 is ignored. The callback returns a valid
8-byte-aligned 16-byte range, disjoint, aliased, or overlapping by one pair.
Callback implementation and FP status/traps are outside scope.
"""
from specs._cr_anim_dof_copy_inputs import calls, inputs as copy_inputs

FUNCTION = "rage::crAnimDofQuaternion::CopyFrom"
ADDRESS = 0x820C4D30
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 2000
FTOL = 0
RET = None
CALLS = calls(15)


def inputs(t):
    copy_inputs(t, overlapping_pairs=True)
