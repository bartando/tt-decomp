"""0x822C73E8: query versus a 64-byte broadphase octree node.

All five shapes, unknown types with null nodes, independently varied padding and
half-width, strict sphere/cylinder/segment faces and asymmetric point faces,
circumscribed sphere/circle rejection, each segment SAT cross axis, degenerate
segments/capsules, y-independent cylinders, ignored w, and NaN/Inf/subnormals.
Capsule calls compare all xyz arguments, including the min/max rounding at large
centres. Execute the original SAT callee on both sides. The two internal-VMX-ABI
helpers are inlined by the portable lift: execute them transparently on the
original side. No original code patches, ignored memory, or float tolerance.
VMX dot/flush and multiply-add rounding follow lift-check, not console evidence.
"""
from liftcheck.spec import *

FUNCTION = "rage::phLevelNew_QueryOverlapsNode"
ADDRESS = 0x822C73E8
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 2000
FP_CONTRACT = "off"
CALLS = {
    0x822C4EB8: run(transparent=True),
    0x822C4E30: run(transparent=True),
    0x8223E648: run(),
}


def inputs(t):
    rng = t.rng
    node = t.alloc(0x40, "node", ctype="phLevelBroadphaseNode")
    query = t.alloc(0x40, "query", ctype="phLevelQuery")
    kind = rng.randrange(5)
    case = rng.randrange(64)
    centre = [rng.uniform(-8, 8) for _ in range(4)]
    start = [rng.uniform(-12, 12) for _ in range(4)]
    end = [rng.uniform(-12, 12) for _ in range(4)]
    half_width = rng.uniform(0, 5)
    padding = rng.uniform(0, 3)
    length = rng.uniform(0, 8)
    radius = rng.uniform(0, 3)

    if case < 18:
        # Faces on each axis, either side, exact/just inside/just outside.
        # Sphere/cylinder must exclude both faces; point includes only upper.
        kind = rng.choice((0, 2, 4))
        axis = (case // 6) if kind != 2 else rng.choice((0, 2))
        side = -1 if (case // 3) % 2 else 1
        delta = (0, -2**-20, 2**-20)[case % 3]
        centre = [0, 0, 0, rng.uniform(-100, 100)]
        half_width, padding, end[0] = 1, 1, 1
        extent = half_width if kind == 4 else half_width + padding + end[0]
        start[:3] = [0, 0, 0]
        start[axis] = side * (extent + delta)
        if kind == 2:
            start[1] = rng.choice((-1e20, 1e20, float("nan")))
    elif case < 22:
        # Corners inside every expanded axis but outside the circumscribed
        # sphere/circle. A large query radius makes these rejection paths real.
        kind = 0 if case < 20 else 2
        centre = [0, 0, 0, 99]
        half_width, padding, end[0] = 0.5, 0.5, 3
        start[:3] = [3.9, 3.9 if kind == 0 else 999, 3.9]
        if case % 2:
            start[0] = -start[0]
    elif case < 34:
        kind = 1
        centre = [0, 0, 0, rng.uniform(-100, 100)]
        half_width, padding = 0.5, 0.5
        start[:3], end[:3] = [-3, 0, 0], [3, 0, 0]
        axis = (case - 22) // 4
        other = (axis + 1) % 3
        # Crossing, face tangency, tiny inside/outside, and zero length.
        face = (0, 1, 1 - 2**-20, 1 + 2**-20)[case % 4]
        start[axis], end[axis] = -3, 3
        start[other] = end[other] = face
        if case == 33:
            end[:3] = start[:3]
    elif case < 37:
        # Every segment coordinate range intersects the cube but a separating
        # cross axis rejects it. Rotate to cover yz/zx/xy independently.
        kind = 1
        centre, half_width, padding = [0, 0, 0, 77], 1, 0
        axis = case - 34
        a, b = (axis + 1) % 3, (axis + 2) % 3
        start[:3], end[:3] = [0, 0, 0], [0, 0, 0]
        start[a], start[b], end[a], end[b] = 0, 3, 3, 0
    elif case < 43:
        kind = 3
        centre, half_width, padding = [2, -3, 4, 71], 1, 0.5
        start[:3], end[:3] = [-3, -3, 4], [1, 0, 0]
        length = (0, 1, 4, 8, -2, 2)[case - 37]
        radius = (0, 0.5, 1, 2, -1, 1)[case - 37]
        if case == 42:
            end[:3] = [0, 0, 0]
    elif case < 46:
        # Scalar min/max at large centres can cancel or quantize the box.
        kind = 3
        centre = [rng.choice((-1, 1)) * 2**rng.randrange(22, 28) for _ in range(4)]
        half_width, padding = rng.choice((0, 0.5, 1, 3)), rng.choice((0, 0.25, 2))
        start[:3] = centre[:3]
    elif case < 50:
        kind = rng.choice((-1, 5, 6, 0x7fffffff, -0x80000000))
        node = 0  # Unknown shapes must not dereference the node at all.
    elif case < 55:
        half_width, padding = rng.choice((0, -1, 1)), rng.choice((0, -2, 2))
        end[0], radius, length = rng.choice((0, -1, 1)), rng.choice((0, -1)), 0
    elif case < 61:
        special = rng.choice((float("nan"), float("inf"), -float("inf"),
                              -0.0, 2**-149, -2**-126, 2**-80))
        slot = case - 55
        if slot == 0:
            start[rng.randrange(4)] = special
        elif slot == 1:
            end[rng.randrange(4)] = special
        elif slot == 2:
            centre[rng.randrange(4)] = special
        elif slot == 3:
            half_width = special
        elif slot == 4:
            padding = special
        else:
            length, radius = special, special
    else:
        # Finite xyz, poisoned w lanes: never part of any geometric decision.
        start[3], end[3], centre[3] = float("nan"), float("inf"), -float("inf")

    for lane in range(4):
        t.wf32(query + 4 * lane, start[lane])
        t.wf32(query + 0x10 + 4 * lane, end[lane])
        if node:
            t.wf32(node + 0x20 + 4 * lane, centre[lane])
    if node:
        t.wf32(node, padding)
        t.wf32(node + 0x30, half_width)
    t.wf32(query + 0x20, length)
    t.wf32(query + 0x24, radius)
    t.w32(query + 0x30, kind)
    t.args(r3=node, r4=query)
