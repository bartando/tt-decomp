"""Slot 13: tagged lookup, native/script dispatch and optional stack result.

Lookup and callbacks are boundary models with exact argument checks, deliberate
side effects and dirty upper return bits. Retail stack-pop executes on both
sides, including all eight bytes and depth updates. Cover missing methods,
all callable/noncallable tags, signed depth comparisons, no/one/multiple pushed
values and independently randomized callback results. No ignores or tolerance;
script bytecode, lookup internals and the logger body are outside this spec.
"""
import struct
from liftcheck.spec import *

FUNCTION = "rage::swfSCRIPTOBJECT::Invoke"
ADDRESS = 0x823FEA28
SOURCE = "src/rage/swf.cpp"
TRIALS = 1600
RET = None
EXTERNS = {"rage_DebugLog": 0x8240E6D0, "swfPopResult": 0x82403270}
DEPTH = 0x82604D1C
STACK = 0x82715C98


def word(ctx, addr):
    return int.from_bytes(ctx.read(addr, 4), "big")


def lookup(ctx):
    obj = ctx.r(3)
    assert ctx.read(ctx.r(4), 8) == ctx.read(obj + 4, 4) + struct.pack(">I", 1), "type-1 method key"
    assert ctx.read(ctx.r(5), 8) == struct.pack(">II", 0, 7), "type-7 empty lookup result"
    ctx.write(ctx.r(5), ctx.read(obj + 12, 8))
    # Lookup can itself change the stack depth; the snapshot must follow it.
    ctx.write(DEPTH, ctx.read(obj + 36, 4))
    ctx.write(obj + 48, ctx.read(obj + 48, 4)[::-1])
    ctx.ret(r3=word(ctx, obj + 8))


def native(ctx):
    obj = ctx.r(3)
    assert (ctx.r(4), ctx.r(5), ctx.r(6)) == (word(ctx, obj + 20), word(ctx, obj + 24), word(ctx, obj + 28))
    assert ctx.read(ctx.r(6), 8) == struct.pack(">II", 0, 5), "default initialized before native call"
    ctx.write(ctx.r(6), ctx.read(obj + 40, 8))
    ctx.write(ctx.r(4), ctx.read(obj + 40, 8))


def execute(ctx):
    callable_obj, obj = ctx.r(3), ctx.r(6)
    assert callable_obj == word(ctx, obj + 12)
    assert (ctx.r(4), ctx.r(5), ctx.r(7)) == (word(ctx, obj + 20), word(ctx, obj + 24), 0)
    assert ctx.read(word(ctx, obj + 28), 8) == struct.pack(">II", 0, 5), "default initialized before script call"
    ctx.write(DEPTH, ctx.read(obj + 32, 4))
    ctx.write(ctx.r(4), ctx.read(callable_obj + 4, 8))


CALLS = {"object.vfn_10": model(lookup, args=("r3", "r4", "r5"), deref={"r4": 8}),
         "native": model(native, args=("r3", "r4", "r5", "r6")),
         "callable.vfn_14": model(execute, args=("r3", "r4", "r5", "r6", "r7")),
         0x82403270: run(args=("r3",)),
         0x8240E6D0: stub(ret="void", args=("r3", "r4"))}


def inputs(t):
    r = t.rng
    obj = t.alloc(64, "scriptObjectAndModelState")
    result = t.alloc(16, "resultAndGuards") + 4
    args = t.alloc(48, "argumentsAndGuards") + 4
    callable_obj = t.alloc(16, "callableObject")
    t.w32(callable_obj, t.vtable("callable"))
    t.w32(obj, t.vtable("object"))
    text = r.choice((b"", b"play", b"onEnterFrame", b"CustomMethod", b"method_" * 50))
    name = t.alloc(len(text) + 1, "methodName", fill=text + b"\0")
    t.w32(obj + 4, name)
    # Low byte alone determines success, including dirty high bits on failure.
    status = (0, 1, 0x100, 0x101, 0x80, 0xff, 0xdeadbe00, 0xabcdef02)[t.index % 8]
    tag = (6, 5, 0, 1, 2, 3, 4, 7, 0x105, 0x106, 0xffffffff)[(t.index // 8) % 11]
    t.w32(obj + 8, status)
    t.w32(obj + 12, t.fake_fn("native") if tag == 6 else callable_obj if tag == 5 else t.u32())
    t.w32(obj + 16, tag)
    count = r.choice((0, 1, 2, 4, 0xffffffff, 0x80000000, t.u32()))
    t.w32(obj + 20, args)
    t.w32(obj + 24, count)
    t.w32(obj + 28, result)
    # Keep positive final depths bounded when retail pop will run. Negative
    # depths exercise signed comparisons without indexing before the stack.
    before, after = r.choice(((0, 0), (0, 1), (2, 3), (2, 5), (3, 2),
                              (4, 4), (0x80000000, 0x80000000),
                              (0x7fffffff, 0x80000000), (0xffffffff, 0)))
    t.w32(obj + 32, after)
    t.w32(obj + 36, before)
    t.w32(DEPTH, r.randrange(8))  # May differ from post-lookup depth.
    for i in range(8):
        t.w32(STACK + 8 * i, t.u32())
        t.w32(STACK + 8 * i + 4, t.u32())
    t.args(r3=obj, r4=name, r5=args, r6=count, r7=result)
