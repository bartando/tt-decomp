"""0x82147A88, misnamed SinglesNetworkClient_7A88_2hr: clip a polygon to one plane.

No callees are stubbed and no memory is ignored. Exact float comparison (FTOL=0).
Covers closed last-to-first edges, either crossing direction, complete acceptance/
rejection, plane-boundary and repeated vertices, 0/negative/1/2 counts, arbitrary
fourth lanes, oblique planes, and unordered distances from NaN/infinity.

Limits: aligned, disjoint input/output/plane/count storage and sufficient output
capacity; invalid pointers and counts that overflow address arithmetic are outside
the caller's contract. Scalar inputs exclude subnormals and finite overflow; this
does not establish Xenon's denormal/NaN-payload behavior versus the G4/VMX model.
The original reads a predecessor even for nonpositive counts; those cases provide
readable padding, while the lift returns without the unobservable read.
"""

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::clipPolygonToPlane"
ADDRESS = 0x82147A88
SOURCE = "src/rage/math/polygon_clip.cpp"
TRIALS = 2000


def inputs(t):
    rng = t.rng
    mode = rng.randrange(12)
    count = rng.choice([0, -1, -3, 1, 2, 3, 4, 8, 16]) if mode == 0 else rng.randint(1, 24)
    # Negative and zero counts still load vertices[count - 1] before blelr.
    storage = t.alloc(16 * (max(count, 1) + 4), "inputWithPrefix")
    vertices = storage + 4 * 16
    output = t.alloc(16 * (2 * max(count, 1) + 2), "output", floats=[(0, 4 * (2 * max(count, 1) + 2))])
    output_count = t.alloc(4, "outputCount")
    plane = t.alloc(16, "plane")

    normal = [1.0, 0.0, 0.0, 0.0] if mode < 9 else [rng.uniform(-4, 4) for _ in range(4)]
    if mode == 8:
        normal = [0.0, 0.0, 0.0, rng.choice([-1.0, 0.0, 1.0])]
    for lane, value in enumerate(normal):
        t.wf32(plane + 4 * lane, value)

    previous = None
    for i in range(max(count, 0)):
        point = [rng.uniform(-64, 64) for _ in range(4)]
        if mode == 1:
            point[0] = -rng.uniform(1, 64)       # all inside
        elif mode == 2:
            point[0] = rng.uniform(1, 64)        # all outside
        elif mode == 3:
            point[0] = (-1 if i % 2 else 1) * rng.uniform(1, 64)
        elif mode == 4:
            point[0] = rng.choice([-0.0, 0.0, -1.0, 1.0])
        elif mode == 5 and previous is not None and rng.random() < 0.6:
            point = previous[:]                # degenerate edges
        elif mode == 6:
            point[0] = rng.choice([float("nan"), float("inf"), -float("inf"), -1.0, 1.0])
        elif mode == 7:
            point[3] = rng.choice([0.0, -0.0, float("nan"), float("inf"), -float("inf")])
        for lane, value in enumerate(point):
            t.wf32(vertices + 16 * i + 4 * lane, value)
        previous = point

    # r3 is not dereferenced, so deliberately leave its randomized entry value.
    t.args(r4=count, r5=vertices, r6=output_count, r7=output, r8=plane)
