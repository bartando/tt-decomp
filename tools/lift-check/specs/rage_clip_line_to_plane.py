"""Clip a two-vertex segment against a plane (0x82147BF8).

Aligned, disjoint buffers; finite normal-range inputs and unordered distances are
covered. Subnormals, finite overflow and NaN payload differences are out of scope.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::clipLineToPlane"
ADDRESS = 0x82147BF8
SOURCE = "src/rage/math/polygon_clip.cpp"
TRIALS = 2000


def inputs(t):
    rng = t.rng
    vertices = t.alloc(32, "vertices")
    output = t.alloc(32, "output", floats=[(0, 8)])
    count = t.alloc(4, "outputCount")
    plane = t.alloc(16, "plane")
    mode = rng.randrange(9)
    normal = [1.0, 0.0, 0.0, 0.0] if mode < 8 else [rng.uniform(-4, 4) for _ in range(4)]
    for i, value in enumerate(normal):
        t.wf32(plane + 4 * i, value)
    points = [[rng.uniform(-32, 32) for _ in range(4)] for _ in range(2)]
    signs = [(-1, -1), (1, 1), (-1, 1), (1, -1), (0, 1), (0, -1)]
    if mode < 6:
        for point, sign in zip(points, signs[mode]):
            point[0] = sign * rng.uniform(1, 32)
    elif mode == 6:
        points[rng.randrange(2)][0] = float('nan')
    elif mode == 7:
        points[rng.randrange(2)][3] = rng.choice([float('nan'), float('inf'), -float('inf')])
    for i, point in enumerate(points):
        for lane, value in enumerate(point):
            t.wf32(vertices + 16 * i + 4 * lane, value)
    t.args(r4=rng.choice([-1, 0, 1, 2, 7]), r5=vertices, r6=count, r7=output, r8=plane)
