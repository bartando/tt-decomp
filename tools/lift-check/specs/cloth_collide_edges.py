"""0x82338D28: translate both cloth-edge endpoints away from capsule axes.

No stubs, instruction patches, or ignored memory. Exercise type-9 dispatch,
triplet rounding, signed/empty ranges, indirect/wrapped indices, both capsule
types, retained bound state, sequential shared endpoints, self-edges, midpoint
taper, unclamped axis projection, clamped edge projection, parallel/degenerate
geometry, per-lane selects, alignment, NaNs/infinities, and VMX DAZ/FTZ.

Nonempty first ranges use type 1/13: other types read uninitialized stack state
in the original. Arbitrary aliasing with controller/index metadata is outside
this spec. VMX reciprocal/rsqrt estimates and dot3 precision are the emulator's,
not measurements on Xenon; NaN payload/sign equality is not established.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "clothCollideEdges"
ADDRESS = 0x82338D28
SOURCE = "src/game/match/lvl_table.cpp"
FP_CONTRACT = "off"
FTOL = 1e-6
TRIALS = 1200


def f32(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def vector(t, address, values):
    for lane, value in enumerate(values):
        t.wf32(address + lane * 4, value)


def inputs(t):
    rng = t.rng
    case = rng.randrange(40)
    self = t.alloc(0x120, "cloth", ctype="ClothEdgeCollisionView")
    instance = t.alloc(8, "instance")
    owner = t.alloc(16, "boundOwner")
    composite = t.alloc(0x80, "composite")
    children = t.alloc(4 * 4, "children")
    bounds = [t.alloc(0xF0, f"bound{i}") for i in range(4)]
    ranges = t.alloc(4 * 12, "ranges")
    edges = t.alloc(12 * 8, "edges")
    indices = t.alloc(16 * 4, "edgeIndices")
    positions = t.alloc(8 * 16, "positions")
    words = rng.choice((1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12))
    margin = rng.uniform(-0.2, 0.4)
    if case < 18:
        margin = 0.0
    t.w32(self, instance)
    t.w32(instance + 4, owner)
    t.w32(owner + 12, composite)
    t.w8(composite + 4, 9)
    t.w32(composite + 0x70, children)
    t.w32(self + 0x0C, edges)
    t.w32(self + 0x1C, positions + rng.randrange(16))
    t.wf32(self + 0x80, margin)
    t.w32(self + 0x110, ranges)
    t.w16(self + 0x114, words)
    t.w32(self + 0x118, indices)
    axis = [1.0, 0.0, 0.0, 0.0]
    start = [0.0] * 4
    radius = [1.0] * 4
    slope = [0.25] * 4
    points = [[rng.uniform(-3, 3) for _ in range(4)] for _ in range(8)]
    if case < 12:
        # Axis x, edge y: exact interior/below/above edge-parameter cases.
        x = rng.choice((-4.0, 0.0, 4.0))  # axis parameter is NOT clamped
        z = (0.5, 1.0, 2.0, 0.0)[case % 4]
        y0, y1 = ((-2.0, 2.0), (1.0, 3.0), (-3.0, -1.0))[case // 4]
        points = [[x, y0 if i % 2 == 0 else y1, z, float(i)] for i in range(8)]
    elif case == 12:
        points = [[float(i), 0.5, 0.0, 7.0] for i in range(8)]  # parallel
    elif case == 13:
        points = [[0.0, 0.5, 0.0, -0.0]] * 8  # degenerate/self edges
    elif case == 14:
        axis = [0.0] * 4
    elif case == 15:
        points = [[0.0, 0.0, 0.0, -0.0]] * 8  # zero distance
    elif case == 16:
        points = [[0.0, 1e-7, 0.0, 1.0], [1.0, 1e-7, 0.0, 2.0]] * 4
    elif case == 17:
        points = [[0.0, 1e-5, 0.0, 1.0], [1.0, 1e-5, 0.0, 2.0]] * 4
    elif case == 18:
        radius = [0.25, 1.0, 2.0, 4.0]
        axis = [0.5, -0.25, 0.75, 3.0]
        slope = [-0.5, 0.0, 0.25, 0.75]
    elif case == 19:
        margin = float("nan")
        t.wf32(self + 0x80, margin)
    elif case == 20:
        axis[0] = float("nan")
    elif case == 21:
        axis[1] = float("inf")
    elif case == 22:
        radius = [float("nan"), float("inf"), -float("inf"), -0.0]
    elif case == 23:
        slope = [float("nan"), float("inf"), -float("inf"), 0.0]
    elif case == 24:
        points[0][0] = float("nan")
    elif case == 25:
        points[1][1] = float("inf")
    elif case == 26:
        for point in points:
            point[3] = float("nan")  # dot3 must exclude w
    elif case == 27:
        axis = [1.0, f32(0x007FFFFF), 0.0, -0.0]
        radius = [f32(1), f32(0x807FFFFF), -0.0, f32(1)]
    elif case == 28:
        points = [[f32(0x00800001), f32(1), 0.0, f32(1)],
                  [f32(0x00800000), f32(0x807FFFFF), -0.0, f32(0x807FFFFF)]] * 4
    elif case == 29:
        points = [[0.0, f32(0x1A000000), 0.0, 0.0], [1.0, f32(0x1A000000), 0.0, 0.0]] * 4
    elif case == 30:
        points[0] = [f32(0x7F7FFFFF), 1.0, 2.0, 0.0]
    elif case == 31:
        axis = [rng.uniform(-2, 2) for _ in range(4)]
        start = [rng.uniform(-2, 2) for _ in range(4)]
        radius = [rng.uniform(-1, 3) for _ in range(4)]
    for i, point in enumerate(points):
        vector(t, positions + i * 16, point)
        if case == 28:
            # FTOL must not hide a subnormal w surviving the final VMX add.
            # This lane is selected to zero before the position update.
            t.float_words.discard(positions + i * 16 + 12)
    for i, bound in enumerate(bounds):
        t.w32(children + i * 4, bound)
        kind = rng.choice((1, 13)) if case >= 18 else (1 if case % 2 == 0 else 13)
        if case == 32 and i > 0:
            kind = 7  # retained state after a valid first bound
        t.w8(bound + 4, kind)
        vector(t, bound + 0x70, radius)
        vector(t, bound + 0x90, start)
        vector(t, bound + 0xB0, axis)
        vector(t, bound + 0xC0, start)
        vector(t, bound + 0xE0, axis)
        vector(t, bound + 0xA0, slope)
        first, end = rng.randrange(4), rng.randrange(4, 17)
        if case == 33:
            first, end = rng.choice(((0, 0), (4, 2), (0x7FFFFFFF, -1), (1, -0x80000000)))
        if case == 34 and i == 0:
            first, end = 0, 0  # empty type-1 still seeds the following range
            t.w8(bound + 4, 1)
        t.w32(ranges + i * 12, i | (rng.randrange(4) << 30))
        t.w32(ranges + i * 12 + 4, first)
        t.w32(ranges + i * 12 + 8, end)
    for i in range(12):
        a, b = (i * 2) % 8, (i * 2 + 1) % 8
        if case >= 18:
            a, b = rng.randrange(8), rng.randrange(8)
        t.w32(edges + i * 8, a | (rng.randrange(16) << 28))
        t.w32(edges + i * 8 + 4, b | (rng.randrange(16) << 28))
    for i in range(16):
        t.w32(indices + i * 4, rng.randrange(12) | (rng.randrange(8) << 29))
    if case == 35:
        t.w32(self, 0)
        t.w32(self + 0x1C, 0)
    elif case == 36:
        t.w8(composite + 4, rng.choice((0, 1, 3, 12, 13, 255)))
        t.w32(self + 0x110, 0)
    elif case == 37:
        t.w16(self + 0x114, 0)
        t.w32(composite + 0x70, 0)
    elif case == 38:
        # Signed negative cursor, but slwi wraps to a valid input word.
        t.w16(self + 0x114, 1)
        t.w32(self + 0x118, indices + 4)
        t.w32(ranges + 4, -1)
        t.w32(ranges + 8, 2)
    elif case == 39:
        # Both endpoints alias: force correction on a degenerate edge.
        t.w16(self + 0x114, 1)
        t.w32(ranges + 4, 0)
        t.w32(ranges + 8, 1)
        t.w32(indices, 0)
        t.w32(edges, 0)
        t.w32(edges + 4, 0)
    t.args(r3=self)
