"""Slot 11 forwards the tagged key/value and full status through inner+0x1CA4.

The inner object is non-null, as required by the original thunk. Model only the
inner setter; its arbitrary 32-bit status must survive the forwarding call.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfACTIONFUNC::SetMember"
ADDRESS = 0x823FF4A0
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
RET = "r3"


def _set(ctx):
    ctx.write(ctx.r(3) + 4, ctx.read(ctx.r(5), 8))
    ctx.ret(r3=ctx.rng.choice((0, 1, 0x100, 0xFFFFFFFF, ctx.rng.getrandbits(32))))


CALLS = {"inner.vfn_11": model(_set, args=("r3", "r4", "r5"), deref={"r4": 8, "r5": 8})}


def inputs(t):
    obj = t.alloc(0x1CB0, "action")
    inner = t.alloc(16, "inner")
    t.w32(inner, t.vtable("inner"))
    t.w32(obj + 0x1CA4, inner)
    t.args(r3=obj, r4=t.alloc(8, "key"), r5=t.alloc(8, "value"))
