"""0x823389E8: cloth collision against a type-13 tapered capsule.

Run both original callees, using the capsule spec's VMX argument bridges; compare
all call arguments/vector lanes, call order, and external writes. No instruction
patches, ignored memory, or modeled collision/filtering. Cover padded batches,
endcaps and taper, strict radial/axial boundaries, first-index suppression,
repeated other indices, signed movable thresholds, mode-1 response, nonuniform
lanes (including discarded w radius), unaligned vectors, empty groups, NaNs,
infinities, zero-length normals, subnormals, and live reduction/origin aliasing.

Limits: VMX estimates use the checker's exact reciprocal/rsqrt and dot3 its
double accumulation. FTOL permits estimate/refinement rounding and numerical NaN
comparison, not payload/sign equality. Console estimate bits and runtime bridge
integration are not established by these emulator comparisons.
"""
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cloth_collide_capsule import CALLS, f32, vector

FUNCTION = "clothCollideTaperedCapsule"
ADDRESS = 0x823389E8
SOURCE = "src/game/match/lvl_table.cpp"
FP_CONTRACT = "off"
FTOL = 1e-6
TRIALS = 1200


def inputs(t):
    rng = t.rng
    case = rng.randrange(36)
    count = rng.choice((0, 1, 31, 32, 33, 63, 64, 65, 96))
    if case < 15:
        count = rng.choice((1, 31, 33, 65))
    padded = (count + 31) & ~31
    self = t.alloc(0x170, "cloth", ctype="ClothCapsuleCollisionView")
    bound = t.alloc(0xF0, "taperedCapsule", ctype="ClothTaperedCapsuleBoundView")
    groups = t.alloc(4 * 8, "groups")
    indices = t.alloc(max(16, padded * 4), "indices")
    positions = t.alloc(16 * 16, "positions")
    previous = t.alloc(16 * 16, "previousPositions")
    reduction = t.alloc(16, "reduction")
    expansion = t.alloc(16, "expansion")
    group = rng.randrange(4)
    t.w32(self + 0x108, groups)
    t.w32(groups + group * 8, indices)
    t.w16(groups + group * 8 + 4, count)
    t.w16(groups + group * 8 + 6, rng.getrandbits(16))

    first_movable = rng.choice((-0x80000000, -1, 0, 1, 7, 15, 16, 0x7FFFFFFF))
    mode = rng.choice((0, 1, 2, 0xFFFF, 0xABCD0001, 0x10000))
    lower, upper, end = [1.0] * 4, [0.5] * 4, [2.0] * 4
    slope, scale = [0.25] * 4, [math.sqrt(1 - 0.25 ** 2)] * 4
    start, axis, center = [0.0] * 4, [1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]
    pad, shrink = [rng.uniform(0, 0.4)] * 4, [rng.uniform(-0.2, 0.4)] * 4
    broad = 5.0
    if case < 15:
        first_movable, mode = 0, 0
        pad, shrink = [0.0] * 4, [0.0] * 4
    if case in (0, 1, 2, 3, 4, 5, 6, 7, 8):
        # Zero taper gives exact endpoint and radial boundaries. The other
        # cases retain the taper, including exact axial split coordinates.
        slope, scale, upper = [0.0] * 4, [1.0] * 4, [1.0] * 4
    elif case == 15:
        # Per-lane selects are retained until the two vmrghw parameter packs.
        lower, upper, end = [1.5, 1.0, 2.0, 0.0], [0.5, 0.75, 1.0, 0.0], [2, 1, 3, 4]
        slope, scale = [0.25, -0.5, 0.125, 0.75], [0.9, 0.8, 0.7, 0.6]
        pad, shrink = [0.1, 0.3, 0.2, 0.4], [-0.5, 0.0, 0.5, 1.0]
    elif case == 16:
        pad[2] = float("nan")
    elif case == 17:
        lower[1] = float("nan")
    elif case == 18:
        axis[2] = float("nan")
    elif case == 19:
        end = [float("nan"), float("inf"), -float("inf"), -0.0]
    elif case == 20:
        shrink = [float("nan"), float("inf"), -float("inf"), -0.0]
        first_movable = 0
    elif case == 21:
        pad = [float("inf")] * 4
    elif case == 22:
        broad, pad = f32(1), [f32(0x807FFFFF)] * 4
    elif case == 23:
        # DAZ on the axis and FTZ after a subtraction/multiply both matter.
        axis = [1.0, f32(0x007FFFFF), 0.0, -0.0]
        start, end = [-1.0e38, 0.0, 0.0, 0.0], [1.0e38] * 4
        lower, upper, slope, scale = [2.0] * 4, [2.0] * 4, [0.0] * 4, [1.0] * 4
        first_movable, mode, pad, shrink = 0, 0, [0.0] * 4, [0.0] * 4
    elif case == 24:
        broad = float("nan")
    elif case == 25:
        # w radius is masked, unlike clothCollideCapsule's four-lane test.
        lower, upper, pad = [2.0, 2.0, 2.0, 0.0], [2.0, 2.0, 2.0, 0.0], [0.0] * 4
        slope, scale = [0.0] * 4, [1.0] * 4
        first_movable = 0
    elif case in (26, 30, 31, 32, 35):
        start = [rng.uniform(-1, 1) for _ in range(4)]
        axis = [rng.uniform(-1, 1) for _ in range(3)] + [0.0]
        norm = math.sqrt(sum(x * x for x in axis[:3]))
        axis = [x / norm for x in axis]
        center = [start[i] + axis[i] for i in range(4)]
        first_movable, mode = 0, 1
    elif case == 33:
        # Strict broad boundary: the center-relative xyz distance is 25.
        lower, upper, pad = [10.0] * 4, [10.0] * 4, [0.0] * 4
    elif case == 34:
        # Subnormal slope amplified by a large end radius.
        slope, upper, end = [f32(0x007FFFFF)] * 4, [1.0e38] * 4, [0.0] * 4
        first_movable, mode, pad = 0, 0, [0.0] * 4

    for i in range(16):
        point = [rng.uniform(-2, 4), rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(-2, 2)]
        if case < 15:
            point = [(-1.0, 0.0, 0.25, 1.0, 2.0, 2.125, 3.0)[i % 7],
                     (0.0, 0.5, 1.0, f32(0x3F7FFFFF), f32(0x3F800001))[case % 5],
                     0.0, float(i % 3)]
            if case == 5:
                point = [1.0, 0.0, 0.0, -0.0]
            elif case == 6:
                point = [1.0, f32(0x1A000000), 0.0, 0.0]
            elif case == 7:
                point[1] = f32(1)
            elif case == 8:
                point[3] = float("nan")
            elif case == 14:
                point = [rng.choice((0.25, 2.125)), 0.25, 0.0, 0.0]
        elif case in (23, 25, 34):
            point = [0.0, 0.5, 0.0, 0.0]
        elif case == 27:
            point[0] = float("nan")
        elif case == 28:
            point[0] = float("inf")
        elif case == 29:
            point = [1.0, 0.5, 0.0, 0.0]
            first_movable = 0
        elif case == 33:
            point = [4.0, 4.0, 0.0, 9.0]
        vector(t, positions + i * 16, point)
        vector(t, previous + i * 16, [rng.uniform(-2, 2) for _ in range(4)])
    for i in range(padded):
        index = rng.randrange(16)
        if case in (0, 5, 11, 29):
            index = (3, 3, 4, 4, 3, 5, 4, 3)[i % 8]
        if case == 30:
            index |= rng.randrange(16) << 28
        t.w32(indices + 4 * i, index)

    t.w32(self + 8, first_movable)
    for offset, values in ((0x40, center), (0x70, lower), (0x80, upper), (0x90, end),
                           (0xA0, slope), (0xB0, scale), (0xC0, start), (0xE0, axis)):
        vector(t, bound + offset, values)
    t.wf32(bound + 8, broad)
    vector(t, expansion, pad)
    vector(t, reduction, shrink)
    t.floats(self + 0x50, 8, -1, 1)
    t.floats(self + 0x70, 4, 0, 3)
    t.floats(self + 0x160, 4, -1, 1)
    transforms = t.alloc(64, "transform")
    transform_indices = t.alloc(4, "transformIndices")
    t.w32(transform_indices, 0)
    t.w32(self + 0x140, transforms)
    t.w32(self + 0x148, transform_indices)
    t.w32(self + 0x150, 0)
    for row in range(4):
        values = [float(row == col) for col in range(4)]
        if case == 35:
            values = [rng.uniform(-1, 1) for _ in range(4)]
        vector(t, transforms + row * 16, values)
    if case == 29:
        reduction = positions + 4 * 16  # response changes later shrink inputs
    elif case == 31:
        previous = positions
    t.w32(self + 0x1C, positions + rng.randrange(16))
    t.w32(self + 0x24, previous + rng.randrange(16))
    if count == 0:
        bound = reduction = expansion = 0
        t.w32(self + 0x1C, 0)
        t.w32(self + 0x24, 0)
        t.w32(groups + group * 8, 0)
    t.args(r3=self, r4=bound, r5=group | (rng.randrange(8) << 29),
           r6=reduction + (rng.randrange(16) if count else 0),
           r7=expansion + (rng.randrange(16) if count else 0), r8=mode)
