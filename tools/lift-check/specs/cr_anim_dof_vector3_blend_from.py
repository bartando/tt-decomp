"""0x820C4898: four-lane VMX blend, copy, and early exit.

The callback returns a 16-byte aligned vector, disjoint from or exactly aliasing
the target. Float comparison ignores NaN payloads and zero signs; FP status
flags and traps are outside scope.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::crAnimDofVector3::BlendFrom"
ADDRESS = 0x820C4898
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 2000
FP_CONTRACT = "off"
RET = None


def source(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 4, 4), "big"))


CALLS = {"source.vfn_14": model(source, args=("r3",))}


def inputs(t):
    rng = t.rng
    target = t.alloc(32, "target")
    source_obj = t.alloc(8, "source")
    vector = t.alloc(16, "sourceVector")
    t.w32(source_obj, t.vtable("source"))
    t.w32(source_obj + 4, rng.choice((vector, vector, target + 16)))
    for lane in range(4):
        for address in (target + 16 + lane * 4, vector + lane * 4):
            t.wf32(address, rng.choice((rng.uniform(-100, 100), 1e-40, -1e-40,
                                        1.1754943508222875e-38, 0.0)))
    factor = rng.choice((0.0, -0.0, -1.0, 1.0, 2.0, float('nan'),
                         1e-40, 0.001, 0.0010001, 0.5, 0.9989999, 0.999,
                         rng.uniform(0.001, 0.999)))
    factor = struct.unpack(">f", struct.pack(">f", factor))[0]
    t.args(r3=target, r4=source_obj, f1=factor)
