"""swfINSTANCE slot 11: display-property writes and delegated script assignment.

Run the original value-to-string and numeric conversion helpers. Stub the text
release/copy, texture lookup and rotation remainder, comparing their arguments
and full string/value pointees. Model delegated setters with observable writes;
exercise low-byte definition status, existing scripts and lazy pool allocation.
No ignored memory or float tolerance.

Limits: keys are non-null direct strings or finite acyclic chunk chains; text
values fit the original 256-byte local buffer; numeric values use byte-bool,
int32, float32 or nonnumeric tags (no CRT string parsing). The pool has a free
node. Callee internals other than conversions are outside this check.
RET=None is deliberate:
the shared C++ SetMember interface is void, but the original returns r3 (1 for
builtins, the script's result otherwise). This ABI defect requires a coordinated
base/override correction and is tracked in KNOWN_WRONG_LIFTS.md.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::swfINSTANCE::SetMember"
ADDRESS = 0x823FC1A8
SOURCE = "src/rage/swf.cpp"
TRIALS = 900
RET = None

PROPERTIES = (
    "_x", "_y", "_xscale", "_yscale", "text", "_alpha", "textColor",
    "_rotation", "__texturename", "__drawcallback", "_seamFix",
    "onEnterFrame", "onRelease", "custom", "_visible", "_name", "_width",
    "_height", "_parent", "this", "_X", "_x_extra", "", "long_key_" * 16,
)


def _definition(ctx):
    ctx.write(ctx.r(3) + 8, ctx.read(ctx.r(5), 8))
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 4, 4), "big"))


def _script(ctx):
    if ctx.read(ctx.r(3), 4) == struct.pack(">I", 0x82074D14):
        assert ctx.read(ctx.r(3) + 4, 12) == bytes(12)
    ctx.write(ctx.r(3) + 8, ctx.read(ctx.r(5), 8))
    ctx.ret(r3=ctx.rng.getrandbits(32))


CALLS = {
    0x823FA768: run(),
    0x823FA688: run(),
    0x823FA5C8: run(),
    0x823F8A38: stub(ret="void", args=("r3", "r4")),
    0x823FABC0: stub(args=("r3",)),
    0x82151990: stub(args=("r3", "r4")),
    0x82431D78: stub(args=("f1", "f2")),
    "definition.vfn_5": model(_definition, args=("r3", "r4", "r5"), deref={"r5": 8}),
    "script.vfn_11": model(_script, args=("r3", "r4", "r5"), deref={"r4": 8, "r5": 8}),
    0x823FC8A8: model(_script, args=("r3", "r4", "r5"), deref={"r4": 8, "r5": 8}),
}


def _string(t, text, name):
    value = t.alloc(8, name)
    if t.rng.randrange(2):
        t.w32(value, t.alloc(len(text) + 1, name + "Text", fill=text + b"\0"))
        t.w32(value + 4, 1)
    else:
        head = 0
        chunks = [text[i:i + 12] for i in range(0, len(text), 12)] or [b""]
        for chunk in reversed(chunks):
            node = t.alloc(16, name + "Chunk", fill=chunk.ljust(12, b"\0"))
            t.w32(node + 12, head)
            head = node
        t.w32(value, head)
        t.w32(value + 4, 0)
    return value


def inputs(t):
    rng = t.rng
    instance = t.alloc(0xD4, "instance")
    definition = t.alloc(16, "definition")
    t.w32(definition, t.vtable("definition"))
    t.w32(definition + 4, rng.choice((0, 1, 0x100, 0x101, 0xFF)))
    t.w32(instance + 4, definition)
    script = t.alloc(16, "existingScript")
    t.w32(script, t.vtable("script"))
    t.w32(instance + 0xA0, rng.choice((0, script)))
    t.w32(instance + 0x48, rng.choice((0, t.alloc(16, "oldText"))))

    pool = t.alloc(16, "scriptPool")
    free_object = t.alloc(16, "freeScriptObject")
    t.w32(free_object, t.alloc(16, "nextFreeScriptObject"))
    t.w16(pool + 6, rng.choice((0, 1, 0xFFFF, rng.randrange(0x10000))))
    t.w32(pool + 12, free_object)
    t.w32(0x82604C60, pool)
    t.w32(0x82606404, t.alloc(16, "textureDictionary"))

    property_name = rng.choice(PROPERTIES)
    key = _string(t, property_name.encode(), "key")
    if property_name == "text":
        value = _string(t, rng.choice((b"", b"HUD", b"abc\0tail", b"t" * 252)), "value")
    elif property_name == "__texturename":
        # The raw payload is a string pointer even when the tag says otherwise.
        text = rng.choice((b"", b"HUD", b"texture_" * 20))
        value = t.alloc(8, "value")
        t.w32(value, t.alloc(len(text) + 1, "textureName", fill=text + b"\0"))
        t.w32(value + 4, rng.choice((0, 1, 2, 3, 4, 5, 0xFFFFFFFF)))
    else:
        value = t.alloc(8, "value")
        tag = rng.choice((2, 3, 4, 5, 6, 7, 0xFFFFFFFF))
        t.w32(value + 4, tag)
        bits = rng.choice((0, 1, 99, 100, 101, 0xFFFFFF9C, 0xFFFFFFFF,
                           0x7FFFFFFF, 0x80000000, 0x3F800000, 0xBF800000,
                           0x43B40000, 0x7F7FFFFF, 0x7F800000, 0xFF800000, 0x7FC12345,
                           rng.getrandbits(32)))
        t.w32(value, bits)
    t.args(r3=instance, r4=key, r5=value)
