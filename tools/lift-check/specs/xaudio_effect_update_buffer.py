from liftcheck.spec import *

FUNCTION = "xaudioEffect_UpdateBuffer"
ADDRESS = 0x8247FBA0
SOURCE = "src/rage/audio/xaudio_effect.cpp"
TRIALS = 1000


def callback(ctx):
    # Modify the buffer passed by reference, as well as checking both words.
    data = ctx.read(ctx.r(3), 8)
    ctx.write(ctx.r(3) + 4, data[:4])

CALLS = {
    "callback": model(callback, args=("r3",), deref={"r3": 8}),
    "effect.vfn_15": stub(ret=123, args=("r3", "r4", "r5")),
    "effect.vfn_20": stub(ret=456, args=("r3", "r4"), deref={"r4": 4}),
}


def inputs(t):
    effect = t.alloc(68, "effect")
    t.w32(effect, t.vtable("effect", slots=21))
    t.w32(effect + 32, t.u32())
    t.w32(effect + 44, t.fake_fn("callback") if t.rng.randrange(2) else 0)
    t.w32(effect + 48, t.u32())
    t.w8(effect + 61, (t.rng.randrange(256) & ~4) | t.rng.choice((0, 4)))
    t.w16(effect + 64, t.rng.choice((0, 1, 2, 65535)))
    t.args(r3=effect)
