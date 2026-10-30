"""0x820C4D80: quaternion blend, hemisphere flip, copy and early exit.

Quaternion components are finite in [-2, 2]. The callback only returns a valid
aligned quaternion, either disjoint from or exactly aliasing the target.
Normalization executes the original helper on both sides, so this checks its input
and effects, not a separate lift of that helper. Float comparison ignores NaN
payloads and zero signs; FP status flags and traps are outside scope.
"""
from liftcheck.spec import *

FUNCTION = "rage::crAnimDofQuaternion::BlendFrom"
ADDRESS = 0x820C4D80
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 2000
FP_CONTRACT = "off"
RET = None


def source(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 4, 4), "big"))


CALLS = {
    "source.vfn_15": model(source, args=("r3",)),
    0x820C42D8: run(),
}


def inputs(t):
    rng = t.rng
    target = t.alloc(32, "target")
    source_obj = t.alloc(8, "source")
    quat = t.alloc(16, "sourceQuaternion")
    t.w32(source_obj, t.vtable("source"))
    t.w32(source_obj + 4, rng.choice((quat, quat, target + 16)))
    for lane in range(4):
        t.wf32(target + 16 + lane * 4, rng.uniform(-2, 2))
        t.wf32(quat + lane * 4, rng.uniform(-2, 2))
    # Cancellation makes the first fused dot-product add change the hemisphere.
    if rng.randrange(8) == 0:
        t.w32(source_obj + 4, quat)
        for lane, (src, dst) in enumerate(zip(
                (0.8630229234695435, 0.0, 0.0, 0.39444732666015625),
                (-0.10346708446741104, 0.0, 0.0, 0.2263786792755127))):
            t.wf32(quat + 4 * lane, src)
            t.wf32(target + 16 + 4 * lane, dst)
        factor = 0.5
    else:
        factor = rng.choice((0.0, -0.0, -1.0, 1.0, 2.0, float('nan'),
                             rng.uniform(0.001, 0.999)))
    t.args(r3=target, r4=source_obj, f1=factor)
