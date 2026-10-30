"""swfINSTANCE slot 10: display properties, definition lookup and lazy script object.

The ABI's r4 is an 8-byte SWF value, despite the old const char* declaration.
Run the original value-to-string helper; model only the delegated lookups, checking
their keys and output state as well as their arguments and writes. No float tolerance.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::swfINSTANCE::GetMember"
ADDRESS = 0x823FB970
SOURCE = "src/rage/swf.cpp"
TRIALS = 600

PROPERTIES = (
    "this", "_root", "_global", "textColor", "_parent", "onEnterFrame",
    "_name", "_x", "_y", "_width", "_height", "_xscale", "_yscale",
    "_alpha", "_rotation",
    # Not handled by this dispatcher: exact matching, empty and long keys too.
    "custom", "_visible", "__drawcallback", "THIS", "_x_extra", "",
    "long_property_" * 8,
)


def _definition(ctx):
    # Every non-builtin lookup preinitializes the output tag, even on failure.
    assert ctx.read(ctx.r(5) + 4, 4) == struct.pack(">I", 4)
    ctx.write(ctx.r(5), ctx.read(ctx.r(3) + 8, 8))
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 4, 4), "big"))


def _script(ctx):
    # Fallback wraps the converted string as a type-1 key on the stack.
    assert ctx.read(ctx.r(4) + 4, 4) == struct.pack(">I", 1)
    if ctx.read(ctx.r(3), 4) == struct.pack(">I", 0x82074D14):
        assert ctx.read(ctx.r(3) + 4, 12) == bytes(12)
        status = ctx.rng.randrange(2)
    else:
        status = int.from_bytes(ctx.read(ctx.r(3) + 4, 4), "big")
    ctx.write(ctx.r(5), ctx.rng.randbytes(8))
    ctx.ret(r3=status)


CALLS = {
    0x823FA768: run(),
    0x823FEF98: stub(args=("r3", "r4")),
    0x823FF0D8: stub(args=("r3", "r4")),
    "definition.vfn_4": model(_definition, args=("r3", "r4", "r5")),
    "script.vfn_10": model(_script, args=("r3", "r4", "r5"), deref={"r4": 8}),
    0x823FBFC0: model(_script, args=("r3", "r4", "r5"), deref={"r4": 8}),
}


def inputs(t):
    rng = t.rng
    instance = t.alloc(0xD0, "instance")
    result = t.alloc(8, "result")
    definition = t.alloc(16, "definition")
    t.w32(definition, t.vtable("definition"))
    t.w32(definition + 4, rng.choice((0, 1, 0x100, 0x101, 0xFF)))
    t.w32(instance + 4, definition)

    script = t.alloc(16, "existingScript")
    t.w32(script, t.vtable("script"))
    t.w32(script + 4, rng.choice((0, 1, 0x100, 0x101, 0xFF)))
    t.w32(instance + 0xA0, rng.choice((0, script)))
    t.w32(instance + 0xB0, rng.choice((0, t.alloc(0xD0, "parent"))))
    for off in (0x54, 0x68, 0x6C, 0x70, 0x74):
        # Include special IEEE encodings; these properties are copied verbatim.
        bits = rng.choice((0, 0x80000000, 0x7F800000, 0xFF800000,
                           0x7FC12345, rng.getrandbits(32)))
        t.w32(instance + off, bits)
    t.w8(instance + 0x4F, rng.choice((0, 1, 127, 128, 254, 255, rng.randrange(256))))

    pool = t.alloc(16, "scriptPool")
    free_object = t.alloc(16, "freeScriptObject")
    next_free = t.alloc(16, "nextFreeScriptObject")
    t.w32(free_object, next_free)
    t.w16(pool + 6, rng.choice((0, 1, 0xFFFF, rng.randrange(0x10000))))
    t.w32(pool + 12, free_object)
    t.w32(0x82604C60, pool)
    t.w32(0x82602828, t.alloc(16, "root"))
    t.w32(0x8260282C, t.alloc(16, "global"))

    text = rng.choice(PROPERTIES).encode()
    key = t.alloc(8, "key")
    if rng.randrange(2):
        t.w32(key, t.alloc(len(text) + 1, "keyText", fill=text + b"\0"))
        t.w32(key + 4, 1)
    else:
        # Type 0: linked chunks of 12 bytes, converted into the global buffer.
        chunks = [text[i:i + 12] for i in range(0, len(text), 12)] or [b""]
        head = 0
        for chunk in reversed(chunks):
            node = t.alloc(16, "keyChunk", fill=chunk.ljust(12, b"\0"))
            t.w32(node + 12, head)
            head = node
        t.w32(key, head)
        t.w32(key + 4, 0)
    t.args(r3=instance, r4=key, r5=result)
