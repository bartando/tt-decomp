"""0x8223BED0: sphere contact against a triangle or quad.

Exercise face/edge/vertex contacts, both rejection paths, all feature indices,
plane/radius equality, signed distances, zero radius, and the small-distance
normal fallback. Compare every output (including writes on a miss) and run
the original fsqrt callee. No ignored ranges or patched original code.

Limits: finite normal-range float32 inputs; no FP exceptions, subnormals,
infinities or NaNs. Known callers use aligned vec4s, disjoint buffers, unit
normals and 3/4 vertices. Also probe non-unit normals and counts -1..2, but
exclude >4 (the original has only four region slots). The emulator's VMX
reciprocal estimate is exact rather than Xenon's estimate. Only the stack
argument locations differ: Xenon SP+0x54/+0x5C, SysV ppc32 SP+8/+12; supply
the same pointers at both locations. radiusSlot retains Xenon's unused r4.
"""
import math
import struct

from liftcheck.spec import *

FUNCTION = "phBoundGeometry_BED0"
ADDRESS = 0x8223BED0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 2000
CALLS = {"crt_sqrt": run()}


def f32(value):
    return struct.unpack(">f", struct.pack(">f", value))[0]


def vector(t, name, values):
    address = t.alloc(16, name)
    for lane, value in enumerate(values):
        t.wf32(address + 4 * lane, value)
    return address


def inputs(t):
    rng = t.rng
    case = rng.randrange(17)
    count = rng.choice([3, 4])
    points = ([[-1, -1, 0, 1], [1, -1, 0, 1], [1, 1, 0, 1], [-1, 1, 0, 1]]
              if count == 4 else [[0, 0, 0, 1], [2, 0, 0, 1], [0, 2, 0, 1]])
    normal = [0.0, 0.0, 1.0, 0.0]
    center = [rng.uniform(-3, 3), rng.uniform(-3, 3), rng.uniform(-1, 1), 1.0]
    radius = rng.uniform(0, 3)
    if case == 0:
        # Face (also signed plane distance and equality at the slab).
        center = [0.25, 0.25, rng.choice([-1, -0.0, 0.0, 0.5, 1]), 1]
        radius = rng.choice([1, 1, 2, abs(center[2])])
    elif case == 1:
        # Project inside each edge, then move outside in its plane.
        edge = rng.randrange(count)
        a, b = points[edge], points[(edge + 1) % count]
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        along = rng.uniform(0.1, 0.9)
        away = rng.choice([0, 0.0001, 0.5, 1, 2])
        center = [a[0] + along * (b[0] - a[0]) + away * (b[1] - a[1]) / length,
                  a[1] + along * (b[1] - a[1]) - away * (b[0] - a[0]) / length,
                  rng.choice([0.0, 0.1, 0.5]), 1]
        radius = rng.choice([0.1, 1, 3])
    elif case == 2:
        # Every vertex, accepted or rejected after the tentative vector writes.
        vertex = rng.randrange(count)
        a = points[vertex]
        middle = [sum(p[i] for p in points) / count for i in range(2)]
        factor = rng.choice([0, 0.0001, 0.5, 1, 2])
        center = [a[i] + factor * (a[i] - middle[i]) for i in range(2)] + [0.25, 1]
        radius = rng.choice([0.25, 0.5, 1, 4])
    elif case == 3:
        center[2] = rng.choice([-2, 2])
        radius = 1
    elif case == 4:
        # Exact coordinates on faces/edges/vertices and zero radius.
        center = list(rng.choice(points))
        radius = rng.choice([0, 0.0001, 1])
    elif case == 5:
        # Reversed winding; the original need not find any candidate.
        points.reverse()
    elif case == 6:
        count = rng.choice([-1, 0, 1, 2])
    elif case == 7:
        # All four lanes matter in the stores, even though dot3 ignores w.
        normal[3] = rng.uniform(-2, 2)
        center[3] = rng.uniform(-4, 4)
        for point in points:
            point[3] = rng.uniform(-4, 4)
    elif case == 8:
        # Non-unit and zero normals.
        normal[2] = rng.choice([0, -1, 0.25, 3])
    elif case == 9:
        # Duplicate vertices / zero-length edges.
        points[rng.randrange(len(points))] = list(points[0])
    elif case == 10:
        # Rotate/translate/scale valid polygons to exercise general xyz math.
        angle = rng.uniform(-math.pi, math.pi)
        c, s = math.cos(angle), math.sin(angle)
        scale = rng.uniform(0.05, 8)
        translation = [rng.uniform(-10, 10) for _ in range(3)]

        def transform(p):
            x, y, z, w = p
            return [translation[0] + scale * (c*x - s*y),
                    translation[1] + scale * (s*x + c*y) * c - scale*z*s,
                    translation[2] + scale * (s*x + c*y) * s + scale*z*c, w]

        points = [transform(p) for p in points]
        center = transform(center)
        normal = [0, -s, c, 0]
        radius *= scale
    elif case == 12:
        # Edge normal fallback: positive plane distance takes the edge branch.
        count = 4
        points = [[-1, -1, 0, 1], [1, -1, 0, 1], [1, 1, 0, 1], [-1, 1, 0, 1]]
        center = [0, -1 - 2**-23, 2**-23, 1]
        radius = 0.5
    elif case == 13:
        # Vertex normal fallback and either side of its squared 1e-12 threshold.
        count = 3
        points = [[0, 0, 0, 1], [2, 0, 0, 1], [0, 2, 0, 1]]
        center = [rng.choice([-1e-7, -6e-7, -9.999999e-7, -1e-6, -1.0000002e-6]),
                  rng.choice([0, -8e-7]), 0, 1]
        radius = 0.5
    elif case == 14:
        # A tangent vertex contact has zero depth; just too small rejects it.
        count = 3
        points = [[0, 0, 0, 1], [2, 0, 0, 1], [0, 2, 0, 1]]
        center = [-0.75, 0, 1, 1]
        radius = rng.choice([1.2499999, 1.25, 1.2500001])
    elif case == 15:
        # Edge-distance rejection/equality after the initial slab accepts.
        count = 4
        points = [[-1, -1, 0, 1], [1, -1, 0, 1], [1, 1, 0, 1], [-1, 1, 0, 1]]
        center = [0, -1.75, 1, 1]
        radius = rng.choice([1.2499999, 1.25, 1.2500001])
    elif case == 16:
        # Zero along-edge distance takes the explicit zero-vector branch.
        count = 4
        points = [[-1, -1, 0, 1], [1, -1, 0, 1], [1, 1, 0, 1], [-1, 1, 0, 1]]
        center = [-1, -2, 1, 1]
        radius = 2

    vertices = t.alloc(64, "vertices")
    for i, point in enumerate(points):
        for lane, value in enumerate(point):
            t.wf32(vertices + i * 16 + lane * 4, value)
    pos = vector(t, "center", center)
    n = vector(t, "normal", normal)
    sphere = vector(t, "spherePoint", [rng.uniform(-9, 9) for _ in range(4)])
    polygon = vector(t, "polygonPoint", [rng.uniform(-9, 9) for _ in range(4)])
    contact = vector(t, "contactNormal", [rng.uniform(-9, 9) for _ in range(4)])
    index = t.alloc(4, "featureIndex")
    depth = t.alloc(4, "depth", floats=[0])
    t.args(r3=pos, f1=f32(radius), r5=vertices, r6=count, r7=n,
           r8=sphere, r9=polygon, r10=index)
    t.w32(t.sp + 0x54, contact)
    t.w32(t.sp + 0x5C, depth)
    t.w32(t.sp + 8, contact)
    t.w32(t.sp + 12, depth)
