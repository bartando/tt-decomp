"""0x82148608: active-frame camera selection and AABB/frustum call forwarding.

Script aspect and clip returns; compare box/matrix/reference bytes and all live
arguments. Mutate active globals and camera data during aspect callback to
verify cached frame selection and subsequent field reloads. Covers cap boundary,
negative near, NaN/infinities, optional references and both boolean returns.
"""
import struct
from liftcheck.spec import *

FUNCTION = "rage::clipAabbToActiveCamera"
ADDRESS = 0x82148608
SOURCE = "src/rage/math/polygon_clip.cpp"
TRIALS = 1200


def _aspect(ctx):
    camera = ctx.r(3)
    ctx.write(0x825C4898, struct.pack(">I", 7))
    ctx.write(camera + 0x340, ctx.read(camera + 0x350, 4))
    ctx.ret(f1=struct.unpack(">d", ctx.read(camera + 0x358, 8))[0])


def _clip(ctx):
    state = ctx.r(3)
    ctx.write(ctx.r(4), ctx.read(state + 16, 48))
    ctx.ret(r3=int.from_bytes(ctx.read(state, 4), "big"))


CALLS = {
    0x82143E98: model(_aspect, args=("r3",)),
    0x821481D8: model(_clip, args=("r3", "r4", "r5", "r10", "f1", "f2", "f3", "f4"),
                      deref={"r4": 48, "r5": 64, "r10": 16}),
}


def inputs(t):
    rng = t.rng
    state = t.alloc(80, "state")
    t.w32(state, rng.randrange(2))
    box = t.alloc(80, "boxAndGuards") + 16
    reference = rng.choice((0, t.alloc(16, "reference")))
    owner = t.alloc(32, "cameraOwner")
    cameras = t.alloc(8 * 912, "frameCameras")
    t.w32(0x8260641C, owner)
    t.w32(owner + 24, cameras)
    index = rng.randrange(7)
    t.w32(0x825C4898, index)
    for frame in range(8):
        camera = cameras + frame * 912
        t.floats(camera + 64, 16, -20, 20)
        t.wf32(camera + 824, rng.uniform(10, 150))
        t.wf32(camera + 836, rng.uniform(1, 1000))
        t.wf32(camera + 832, rng.uniform(0.2, 5))
        t.wf32(camera + 0x350, rng.choice((0., -0., -1., 0.05, 0.1,
                                         0.10000001, 1., float("nan"),
                                         float("inf"), -float("inf"))))
        # The actual aspect getter returns a float in f1.
        aspect = struct.unpack(">f", struct.pack(">f", rng.uniform(0.5, 3)))[0]
        t.wf64(camera + 0x358, aspect)
    t.args(r3=state, r4=box, r5=reference)
