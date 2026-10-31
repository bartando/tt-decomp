from liftcheck.spec import *

FUNCTION = "xaudioEffect_UpdateBuffer"
ADDRESS = 0x8247FBA0
SOURCE = "src/rage/audio/xaudio_effect.cpp"
TRIALS = 1000


def callback(ctx):
    packet = ctx.r(3)
    data = ctx.read(packet, 8)
    # The callback ABI passes one pointer to {context, buffer}. Record both
    # fields as synthetic r4/r5 trace arguments, independently of stack-address
    # normalization and the by-reference buffer write below.
    ctx.rec.gpr[1] = int.from_bytes(data[:4], "big")
    ctx.rec.gpr[2] = int.from_bytes(data[4:], "big")
    ctx.write(packet + 4, data[:4])

CALLS = {
    "effect.update_buffer_callback": model(callback, args=("r3", "r4", "r5"), deref={"r3": 8}),
    "effect.vfn_15": stub(ret=123, args=("r3", "r4", "r5")),
    "effect.vfn_20": stub(ret=456, args=("r3", "r4"), deref={"r4": 4}),
}


def inputs(t):
    effect = t.alloc(68, "effect")
    t.w32(effect, t.vtable("effect", slots=21))
    t.w32(effect + 32, t.alloc(8, "buffer"))
    t.w32(effect + 44, t.fake_fn("effect.update_buffer_callback") if t.index % 3 else 0)
    t.w32(effect + 48, t.alloc(8, "context") if t.index % 2 else 0)
    t.w8(effect + 61, (t.rng.randrange(256) & ~4) | t.rng.choice((0, 4)))
    t.w16(effect + 64, t.rng.choice((0, 1, 2, 65535)))
    t.args(r3=effect)
