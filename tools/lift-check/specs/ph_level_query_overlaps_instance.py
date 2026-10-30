"""0x822DE3D0: collision masks and broadphase query/bound-sphere overlap.

All five shapes, both masks independently (including disjoint nonzero bits),
unknown types with null bounds, strict/inclusive tangencies, segment start/end/
interior and zero length, capsule clamp endpoints, cylinder Y independence,
ignored w lanes, negative/zero radii, NaNs/infinities and subnormals. Random
matrices and nonzero local centroids exercise the transform call's arguments.
Execute the original 0x8228D1D0 transform on both sides; its C++ lift has its
own ph_bound_transform_centroid spec. No ignored memory, code patches or tolerance.
VMX dot rounding/flush behavior is the emulator model, not console evidence.
"""
from liftcheck.spec import *

FUNCTION = "rage::phLevelNew_QueryOverlapsInstance"
ADDRESS = 0x822DE3D0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 2000
FP_CONTRACT = "off"
CALLS = {0x8228D1D0: run()}


def inputs(t):
    rng = t.rng
    query = t.alloc(0x40, "query", ctype="phLevelQuery")
    instance = t.alloc(0x50, "instance")
    archetype = t.alloc(0x18, "archetype")
    bound = t.alloc(0x40, "bound")
    t.w32(instance + 4, archetype)
    t.w32(archetype + 0x0C, bound)
    # Both halves are separately required; high bits and disjoint nonzero masks
    # catch accidental truthiness/OR tests as well as a missing mask.
    type_mask = rng.choice((1, 0x80000000, 0x10000, rng.getrandbits(32) or 1))
    include_mask = rng.choice((8, 0x40000000, 0x100, rng.getrandbits(32) or 1))
    t.w32(archetype + 0x10, type_mask)
    t.w32(archetype + 0x14, include_mask)
    t.w32(query + 0x34, type_mask)
    t.w32(query + 0x38, include_mask)

    case = rng.randrange(40)
    kind = rng.randrange(5)
    start = [rng.uniform(-8, 8) for _ in range(4)]
    end = [rng.uniform(-8, 8) for _ in range(4)]
    centre = [rng.uniform(-8, 8) for _ in range(3)]
    radius = rng.uniform(0, 4)
    length = rng.uniform(0, 8)
    bound_radius = rng.uniform(0, 4)
    local = [0.0, 0.0, 0.0, rng.uniform(-100, 100)]

    if case < 5:
        # Sphere/point/cylinder: inside, exact tangency, just outside, zero and
        # negative radii. Large Y must have no effect on cylinder results.
        kind = rng.choice((0, 2, 4))
        start = [0.0, 0.0, 0.0, rng.uniform(-100, 100)]
        end[0] = rng.choice((0, 1, -1)) if case >= 3 else 1
        bound_radius = rng.choice((0, 1, -1)) if case >= 3 else 1
        distance = bound_radius if kind == 4 else end[0] + bound_radius
        distance += (0, -2**-20, 2**-20, 0, 0)[case]
        centre = [distance, 999 if kind == 2 else 0, 0]
    elif case < 13:
        # Segment projection at/behind start, interior, at/beyond end;
        # zero-length segments still perform the inclusive endpoint test.
        kind = 1
        start = [0, 0, 0, rng.uniform(-100, 100)]
        end = [4, 0, 0, rng.uniform(-100, 100)]
        x = (-1, 0, 1, 2, 4, 5, 0, 4)[case - 5]
        y = rng.choice((0, 1, 1 - 2**-20, 1 + 2**-20, 2))
        centre = [x, y, 0]
        bound_radius = rng.choice((0, 1, 2))
        if case == 11:
            end[:3] = start[:3]
    elif case < 20:
        # Unit axis; each clamp path, exact tangency and degenerate length.
        kind = 3
        start = [0, 0, 0, rng.uniform(-100, 100)]
        end = [1, 0, 0, rng.uniform(-100, 100)]
        length = 4 if case != 19 else 0
        radius = bound_radius = 1
        centre = [[-1, 0, 0], [0, 2, 0], [2, 2, 0], [4, 2, 0],
                  [5, 0, 0], [2, 2 - 2**-20, 0], [2, 0, 0]][case - 13]
    elif case < 24:
        # Reject either mask without touching a null bound, even for known types.
        t.w32(archetype + 0x0C, 0)
        t.w32(archetype + 0x10, 1)
        t.w32(archetype + 0x14, 8)
        t.w32(query + 0x34, (0, 2, 1, 1)[case - 20])
        t.w32(query + 0x38, (8, 8, 0, 4)[case - 20])
    elif case < 26:
        kind = rng.choice((-1, 5, 6, 0x7FFFFFFF, -0x80000000))
        t.w32(archetype + 0x0C, 0)
    elif case < 30:
        # Nontrivial transform and local centroid, not just identity/zero input.
        local[:3] = [rng.uniform(-3, 3) for _ in range(3)]
    elif case < 35:
        special = rng.choice((float("nan"), float("inf"), -float("inf"),
                              -0.0, 2**-149, -2**-126, 2**-80))
        slot = rng.randrange(5)
        if slot == 0:
            start[rng.randrange(4)] = special
        elif slot == 1:
            end[rng.randrange(4)] = special
        elif slot == 2:
            bound_radius = special
        elif slot == 3:
            length = special
        else:
            radius = special

    for lane in range(4):
        t.wf32(query + 4 * lane, start[lane])
        t.wf32(query + 0x10 + 4 * lane, end[lane])
        t.wf32(bound + 0x30 + 4 * lane, local[lane])
    t.wf32(query + 0x20, length)
    t.wf32(query + 0x24, radius)
    t.w32(query + 0x30, kind)
    t.wf32(bound + 8, bound_radius)
    for row in range(4):
        for lane in range(4):
            value = (1.0 if row == lane else 0.0) if row < 3 else (
                centre[lane] if lane < 3 else 1.0)
            if 26 <= case < 30 and row < 3:
                value = rng.uniform(-2, 2)
            t.wf32(instance + 0x10 + 16 * row + 4 * lane, value)
    t.args(r3=query, r4=instance)
