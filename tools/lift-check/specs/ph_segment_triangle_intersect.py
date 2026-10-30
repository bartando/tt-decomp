"""One-sided segment/triangle intersection, including progressive output writes.

Aligned, disjoint vec4s and output pointers; finite normal-range values. Include
boundary hits, both plane rejects, out-of-range fractions, degenerate/back-facing
triangles and both barycentric rejects. Also try arbitrary non-unit normals and
inconsistent direction/end inputs. Xenon and ppc32 use different stack slots.
"""
from liftcheck.spec import *

FUNCTION = "phSegmentTriangleIntersect"
ADDRESS = 0x8223DBC8
SOURCE = "src/physics/ph_physics.cpp"
EXTERNS = {"g_phClampMax": 0x8202D108}
TRIALS = 1500
FP_CONTRACT = "off"


def inputs(t):
    r = t.rng
    case = r.randrange(12)
    a, b, c = [0, 0, 0, 1], [2, 0, 0, 1], [0, 2, 0, 1]
    normal = [0, 0, 1, 0]
    x, y = r.uniform(-1, 3), r.uniform(-1, 3)
    z0, z1 = 1, -1
    if case == 0:
        x, y = r.choice([(0, 0), (2, 0), (0, 2), (1, 1), (0.5, 0.5)])
    elif case == 1:
        z0 = r.choice([-1, -0.001])
    elif case == 2:
        z1 = r.choice([0, 1])
    elif case == 3:
        x, y = r.choice([(-0.5, 0.5), (2.5, 0.1), (0.5, -0.5), (1.5, 1.5)])
    elif case == 4:
        b, c = c, b
    elif case == 5:
        c = [0, r.choice([0, 0.000001, 0.000003, 0.000004, 0.000005]), 0, 1]
    elif case == 6:
        z0 = r.choice([0, 0.000001, 1, 2])
        z1 = r.choice([-1, -0.000001, -2])
    elif case == 7:
        # A fraction beyond one, possible when the zero/one globals differ.
        z0, z1 = 1, -1
        t.wf32(0x8202D108, r.choice([0, 0.25, 0.5, 1]))
    elif case >= 8:
        a = [r.uniform(-4, 4) for _ in range(4)]
        b = [r.uniform(-4, 4) for _ in range(4)]
        c = [r.uniform(-4, 4) for _ in range(4)]
        normal = [r.uniform(-3, 3) for _ in range(4)]
    start = [x, y, z0, r.uniform(-3, 3)]
    end = [x + r.uniform(-1, 1), y + r.uniform(-1, 1), z1, r.uniform(-3, 3)]
    direction = [end[i] - start[i] for i in range(4)]
    if case in (0, 3):
        end[:2] = start[:2]
        direction[:2] = [0, 0]
    if case == 11:
        direction = [r.uniform(-3, 3) for _ in range(4)]

    def vec(name, values):
        p = t.alloc(16, name)
        for i, value in enumerate(values):
            t.wf32(p + 4*i, value)
        return p

    vectors = [vec(name, value) for name, value in zip(
        ("start", "direction", "end", "normal", "a", "b", "c"),
        (start, direction, end, normal, a, b, c))]
    outputs = [t.alloc(4, name, floats=[0]) for name in
               ("startDistance", "endDistance", "fraction")]
    t.args(**dict(zip(("r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10"),
                      vectors + outputs[:1])))
    t.w32(t.sp + 0x54, outputs[1])
    t.w32(t.sp + 0x5c, outputs[2])
    t.w32(t.sp + 8, outputs[1])
    t.w32(t.sp + 12, outputs[2])
