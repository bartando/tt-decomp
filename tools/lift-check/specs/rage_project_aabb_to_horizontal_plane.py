"""0x821493F8 (auto-named phBoundCapsule_93F8_g): horizontal AABB projection.

Run the original box-corner builder. Compare its complete center/size inputs,
all external writes, and the active-camera clip call, including the projected
center and size before that callee can obscure mistakes. Cover auxiliary center
offsets, empty/flat/negative sizes, in-place output, viewpoint translation,
both plane-padding branches and the exact threshold, partial/full clamp and
rejection (including equality), horizontal/zero-length rays, NaNs, infinities,
and VMX denormal flushing. FTOL=0, no ignored memory or patched instructions.

The active-camera clipper is a boundary model, not a proof of that callee. It
captures xyz of center/size/auxiliary, then overwrites center.w and size.w:
the original loads these two words from uninitialized stack slots +108/+124.
Rejections compare every byte without this overwrite. Inputs are aligned;
only the whole input/output boxes may alias. NaN payloads, signed-zero equality,
FP flags/traps, and the console's actual reciprocal estimates are outside scope.
The boundary model canonicalizes computed NaNs on both sides; finite floats
remain byte-exact (a positive harness FTOL would also relax infinity checks).
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::projectAabbToHorizontalPlane"
ADDRESS = 0x821493F8
SOURCE = "src/rage/math/polygon_clip.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def _clip(ctx):
    state, box = ctx.r(3), ctx.r(4)
    assert ctx.r(5) == 0, "reference point must be null"
    for vector in range(2):
        for axis in range(3):
            address = box + vector * 16 + axis * 4
            bits = int.from_bytes(ctx.read(address, 4), "big")
            if bits & 0x7FFFFFFF > 0x7F800000:
                ctx.write(address, struct.pack(">I", 0x7FC00000))
    # Capture the boundary before modifying it, so a rejecting callback cannot
    # hide incorrect projection arithmetic or a clobbered auxiliary vector.
    for vector in range(3):
        ctx.write(state + 16 + vector * 12, ctx.read(box + vector * 16, 12))
    ctx.write(state + 52, ctx.read(box + 44, 4))
    ctx.write(state + 4, struct.pack(">I", 1))
    ctx.write(box + 12, struct.pack(">f", 123.0))
    ctx.write(box + 28, struct.pack(">f", -456.0))
    mode = int.from_bytes(ctx.read(state, 4), "big")
    if mode == 1:
        ctx.write(box, bytes(48))
    elif mode == 2:
        ctx.write(box + 32, struct.pack(">4f", 2.5, -3.5, 4.5, -5.5))
    ctx.ret(r3=mode & 1)


CALLS = {
    0x82147EF8: run(args=("r3", "r4", "r5"), deref={"r4": 16, "r5": 16}),
    0x82148608: model(_clip, args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    kind = rng.randrange(24)
    state = t.alloc(80, "clipState", fill="zero", floats=[(16, 10)])
    t.w32(state, rng.randrange(3))
    source_storage = t.alloc(80, "sourceAndGuards")
    box = source_storage + 16
    output_storage = t.alloc(80, "outputAndGuards")
    output = box if kind == 3 else output_storage + 16
    camera = t.alloc(96, "cameraAndGuards")
    limits = t.alloc(16, "limits")
    t.floats(box, 12, -3, 3)
    t.floats(output, 12, -3, 3)
    t.floats(camera, 24, -20, 20)
    center = [rng.uniform(-8, 8), rng.uniform(1, 8), rng.uniform(-8, 8)]
    size = [rng.uniform(0.1, 8) for _ in range(3)]
    offset = [rng.uniform(-2, 2) for _ in range(3)]
    eye = [rng.uniform(-5, 5), rng.uniform(12, 20), rng.uniform(-5, 5)]
    bounds = [rng.uniform(1, 15), rng.choice((-2., 0., 0.009999999, 0.01, 0.010000001, 2.)),
              rng.uniform(1, 15)]
    if kind == 0:
        size = [rng.choice((0., -0., 2**-149, -(2**-149))) for _ in range(3)]
    elif kind == 1:
        size[rng.randrange(3)] = 0.
    elif kind == 2:
        size[rng.randrange(3)] *= -1
    elif kind in (4, 5):
        # Entirely outside one clamp axis; other axis stays viable.
        center[0 if kind == 4 else 2] = 1000.
    elif kind in (6, 7):
        bounds[0 if kind == 6 else 2] = 0.  # equal min/max must reject
    elif kind == 8:
        bounds[0] = -rng.uniform(1, 4)
    elif kind == 9:
        # At least four rays have y == 0 after subtraction.
        center, offset, size, eye = [0., 1., 0.], [0., 0., 0.], [2., 2., 2.], [0., 2., 0.]
    elif kind == 10:
        # One corner coincides with the viewpoint (infinite rsqrt -> zero).
        center, offset, size, eye = [0., 1., 0.], [0., 0., 0.], [2., 2., 2.], [1., 2., 1.]
    elif kind == 11:
        bounds[rng.choice((0, 1, 2))] = float("nan")
    elif kind == 12:
        center[rng.randrange(3)] = float("nan")
    elif kind == 13:
        eye[rng.randrange(3)] = rng.choice((float("inf"), -float("inf"), float("nan")))
    elif kind == 14:
        bounds[0], bounds[2] = float("inf"), float("inf")
    elif kind == 15:
        # Underflow in dot products/normalization and scalar plane height.
        center, offset, size, eye = [2**-70]*3, [0.]*3, [2**-71]*3, [2**-72]*3
        bounds[1] = 2**-140
    elif kind == 16:
        center, offset, size, eye = [2**70]*3, [0.]*3, [2**69]*3, [0.]*3
    elif kind == 17:
        bounds[1] = eye[1]  # zero plane height collapses the footprint
    elif kind == 18:
        offset = [rng.uniform(-100, 100) for _ in range(3)]
    elif kind == 19:
        size = [0., rng.uniform(1, 4), 0.]  # line input is not the empty case
    elif kind == 20:
        bounds[0] = bounds[2] = 0.25  # clamp both sides
    elif kind == 21:
        bounds[0] = bounds[2] = 1000.  # no clamp
    elif kind == 22:
        size[rng.randrange(3)] = float("nan")
    elif kind == 23:
        bounds[1] = rng.choice((float("inf"), -float("inf")))
    for lane in range(3):
        t.wf32(box + lane * 4, center[lane])
        t.wf32(box + 16 + lane * 4, size[lane])
        t.wf32(box + 32 + lane * 4, offset[lane])
        t.wf32(camera + 64 + lane * 4, eye[lane])
        t.wf32(limits + lane * 4, bounds[lane])
    # Fourth lanes must neither defeat empty detection nor enter the xyz dot.
    for address in (box + 12, box + 28, box + 44, camera + 76, limits + 12):
        t.wf32(address, rng.choice((1., -7., float("nan"), float("inf"))))
    t.args(r3=state, r4=box, r5=camera, r6=output, r7=limits)
