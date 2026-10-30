"""0x82147E18: clip a line against six planes, with optional plane skipping.

Runs the original single-plane clipper on both sides. Inputs are aligned, disjoint,
line segments with sufficient output space; subnormals and VMX NaN-payload
behavior are outside scope.
"""

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::clipLineToFrustum"
ADDRESS = 0x82147E18
SOURCE = "src/rage/math/polygon_clip.cpp"
def copy_bytes(ctx):
    ctx.write(ctx.r(3), ctx.read(ctx.r(4), ctx.r(5)))
    ctx.ret(r3=ctx.r(3))


CALLS = {0x82147BF8: run(), 0x82434520: model(copy_bytes, transparent=True)}
FP_CONTRACT = "off"
TRIALS = 1000


def inputs(t):
    rng = t.rng
    vertices = t.alloc(32, "vertices")
    output_count = t.alloc(4, "outputCount")
    output = t.alloc(16 * 16, "output", floats=[(0, 64)])
    planes = t.alloc(96, "planes")
    reference = t.alloc(16, "reference")
    x = rng.uniform(-4, 4)
    y = rng.uniform(-4, 4)
    w = rng.uniform(0.1, 5)
    h = rng.uniform(0.1, 5)
    z = rng.uniform(-3, 3)
    for i, (px, py) in enumerate([(x-w, y-h), (x+w, y+h)]):
        for lane, value in enumerate((px, py, z, rng.uniform(-5, 5))):
            t.wf32(vertices + 16 * i + 4 * lane, value)
    mode = rng.randrange(6)
    rejection_plane = rng.randrange(6)
    for i in range(6):
        # Axis-aligned or oblique half-spaces, with acceptance and rejection.
        normal = rng.choice([(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0),
                             (0, 0, 1), (0, 0, -1), (1, 1, 0), (-1, 1, 0)])
        offset = rng.uniform(-8, 8)
        if mode == 0:
            normal, offset = (0, 0, 0), -1  # all accepted
        elif mode == 1 and i == rejection_plane:
            normal, offset = (0, 0, 0), 1  # reject outright
        elif mode == 2:
            normal, offset = (0, 0, 0), -1  # all skipped with reference present
        for lane, value in enumerate((*normal, offset)):
            t.wf32(planes + 16 * i + 4 * lane, value)
    for lane in range(4):
        t.wf32(reference + 4 * lane, rng.uniform(-6, 6))
    t.args(r3=0, r4=rng.choice([0, 1, 4, 9, -1]), r5=vertices, r6=output_count,
           r7=output, r8=planes, r9=reference if mode >= 2 else 0)
