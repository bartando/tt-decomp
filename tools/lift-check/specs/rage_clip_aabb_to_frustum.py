"""0x821481D8, formerly phBoundCapsule_81D8_g: world AABB/frustum intersection.

Run the original corner builder, affine inverse, plane builder and polygon
clippers, including sin/cos. Cover empty/flat boxes, acceptance, rejection,
partial intersections, translated/rotated/scaled/sheared cameras, optional
reference points and the 0.1 near-plane cap (including unordered input).
Supplement geometry with scripted clip results to exercise every face/count,
arbitrary fourth lanes, unordered extrema and reloading the camera matrix after
callbacks. The clip call's full quad/planes/reference bytes are compared.

Only center.w and size.w are ignored on trials that can succeed: the original
loads uninitialized stack words at frame+188/+204 before its final vector stores.
The lift preserves those padding words. Empty and scripted-rejection trials
compare every byte, including all three cleared vec4s. FTOL=0; no code patches.
Inputs are aligned, box/matrix/reference do not overlap, clip counts fit the
original 16-vertex scratch buffer. Invalid pointers, traps/FP flags, NaN payload
and signed-zero equality, and real-console VMX rounding are outside this proof.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::clipAabbToFrustum"
ADDRESS = 0x821481D8
SOURCE = "src/rage/math/polygon_clip.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def _u32(ctx, address):
    return int.from_bytes(ctx.read(address, 4), "big")


def _copy_bytes(ctx):
    ctx.write(ctx.r(3), ctx.read(ctx.r(4), ctx.r(5)))
    ctx.ret(r3=ctx.r(3))


class _ClipFace(run):
    def handle(self, ctx):
        state = ctx.r(3)
        mode = _u32(ctx, state)
        if mode == 0:
            return "run"
        face = _u32(ctx, state + 4)
        assert face < 6, "more than six box faces"
        count = _u32(ctx, state + 16 + face * 4)
        ctx.write(ctx.r(6), struct.pack(">I", count))
        if count:
            ctx.write(ctx.r(7), ctx.read(state + 64 + face * 256, count * 16))
        ctx.write(state + 4, struct.pack(">I", face + 1))
        if mode == 3:
            # Original reloads cameraToWorld after each clipper call.
            matrix = _u32(ctx, state + 8)
            ctx.write(matrix + 48, struct.pack(">f", face + 0.25))
        return "return"


CALLS = {
    0x82147EF8: run(args=("r3", "r4", "r5"), deref={"r4": 16, "r5": 16}),
    0x820D7B30: run(args=("r3",), deref={"r3": 64}),
    0x820D7B90: run(args=("r3", "r4"), deref={"r4": 64}),
    0x821480C0: run(args=("r3", "r8", "f1", "f2", "f3", "f4", "f5")),
    0x824301D8: run(args=("f1",)),
    0x824302B0: run(args=("f1",)),
    0x82147D18: _ClipFace(args=tuple(f"r{i}" for i in range(3, 10)),
                          deref={"r5": 64, "r8": 96, "r9": 16}),
    0x82147A88: run(args=tuple(f"r{i}" for i in range(3, 9))),
    # The auto-named 0x82434520 is another memcpy entry point, used by the clipper.
    0x82434520: model(_copy_bytes, transparent=True),
}


def inputs(t):
    rng = t.rng
    kind = rng.randrange(12)
    state = t.alloc(64 + 6 * 256, "clipState", fill="zero")
    storage = t.alloc(80, "boxAndGuards")
    box = storage + 16
    matrix = t.alloc(64, "cameraToWorld")
    reference = t.alloc(16, "referencePoint")
    center = [rng.uniform(-8, 8), rng.uniform(-8, 8), rng.uniform(-30, 5)]
    size = [rng.uniform(0.01, 12) for _ in range(3)]
    if kind == 0:
        size = [rng.choice((0.0, -0.0)) for _ in range(3)]
    elif kind == 1:
        size[rng.randrange(3)] = 0.0  # one zero dimension is not an empty box
    elif kind == 2:
        center, size = [0.0, 0.0, -5.0], [1.0, 1.0, 1.0]
    elif kind == 3:
        center = [1000.0, 1000.0, 1000.0]
    for lane in range(3):
        t.wf32(box + lane * 4, center[lane])
        t.wf32(box + 16 + lane * 4, size[lane])
    # w is deliberately nonzero, and must not defeat the xyz-only empty test.
    t.wf32(box + 12, rng.uniform(-20, 20))
    t.wf32(box + 28, rng.choice((1.0, -7.0, float("nan"), float("inf"))))

    rows = [[1., 0., 0., 0.], [0., 1., 0., 0.], [0., 0., 1., 0.], [0., 0., 0., 1.]]
    if kind in (4, 5, 6, 7, 11):
        axes = rng.sample(range(3), 3)
        for row in range(3):
            rows[row][:3] = [0.] * 3
            rows[row][axes[row]] = rng.choice((-2., -1., 0.5, 1., 2.))
        if kind == 6:
            rows[0][axes[1]] = 0.25
        rows[3][:3] = [rng.uniform(-10, 10) for _ in range(3)]
    for row in range(4):
        for lane in range(4):
            # Non-affine fourth-column bytes are retained by the inverse but ignored
            # by both transforms. NaNs here catch accidental four-column arithmetic.
            value = rows[row][lane] if lane != 3 else rng.choice((0., 1., -3., float("nan")))
            t.wf32(matrix + row * 16 + lane * 4, value)
    t.floats(reference, 4, -25, 25)
    ref = reference if kind in (5, 7, 11) else 0
    near = rng.choice((0., -1., 0.05, 0.1, 0.10000001, 1., float("nan")))
    far = rng.uniform(10, 100)
    fov = rng.choice((30., 60., 90., 120., rng.uniform(10, 150)))
    aspect = rng.uniform(0.5, 2.5)

    if kind in (8, 9, 10, 11):
        t.w32(state, 3 if kind == 11 else 1)
        t.w32(state + 8, matrix)
        active = rng.randrange(6)
        for face in range(6):
            count = (rng.choice((1, 2, 4, 7, 10, 16)) if kind == 10 else
                     rng.randrange(1, 9) if face == active and kind != 8 else 0)
            t.w32(state + 16 + 4 * face, count)
            for vertex in range(count):
                for lane in range(4):
                    value = rng.uniform(-20, 20)
                    if kind == 10 and vertex == 0 and lane < 3:
                        value = rng.choice((float("nan"), float("inf"), -float("inf"), 0.))
                    t.wf32(state + 64 + face * 256 + vertex * 16 + lane * 4, value)
    if kind not in (0, 8):
        t.ignore(box + 12, 4)
        t.ignore(box + 28, 4)
    near, far, fov, aspect = (struct.unpack(">f", struct.pack(">f", x))[0]
                              for x in (near, far, fov, aspect))
    t.args(r3=state, r4=box, r5=matrix, r10=ref,
           f1=near, f2=far, f3=fov, f4=aspect)
