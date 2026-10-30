"""PlaceObject2 execution: child selection, packed matrix and raw color update.

Cover resource placement (slot 7, including null returns), move-only lookup in
sorted lists, missing-depth diagnostics, all four scale/shear flag combinations,
unrelated flag bits, signed halfword limits, null optional data, and both halves
of the color copy. Callback models change command fields to check read timing;
the transform boundary checks the visited byte and all 24 matrix bytes exactly.

Limits: placement and transform decomposition are boundary models, not executed;
this verifies the caller's dispatch, decoding and writes, not pool allocation,
trigonometry, rendering or native performance. Pointers are valid and aligned,
lists are sorted/acyclic with unique uint16 depths, and resource indices are
bounded to an eight-entry table (or 0xFFFF for lookup). Color sources may alias
the destination. No invalid-pointer/fault behavior or concurrent mutation claim.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfCMD_PlaceObject2::Execute"
ADDRESS = 0x824081B0
SOURCE = "src/rage/swf.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
EXTERNS = {"rage_DebugLog": 0x8240E6D0}


def _word(ctx, addr):
    return int.from_bytes(ctx.read(addr, 4), "big")


def _place(ctx):
    parent = ctx.r(3)
    command = _word(ctx, parent + 0xD4)
    child = _word(ctx, parent + 0xD8)
    replacement = _word(ctx, parent + 0xDC)
    # A virtual placement call can rewrite optional data and even the depth
    # used by the diagnostic when it returns null. Read those only afterward.
    for offset, size in ((5, 1), (0x10, 2), (0x18, 8)):
        ctx.write(command + offset, ctx.read(replacement + offset, size))
    if child:
        ctx.write(child + 0xAF, b"\xB7")
    ctx.ret(r3=child)


def _transform(ctx):
    child = ctx.r(3) - 8
    assert ctx.read(child + 0xAF, 1) == b"\x01", "child must be marked before transform"
    ctx.write(child + 8, ctx.read(ctx.r(4), 24))
    command = _word(ctx, child + 0xD4)
    # The caller must reload its color source after transform decomposition.
    ctx.write(command + 0x1C, ctx.read(child + 0xD8, 4))


CALLS = {f"parent.vfn_{slot}": fail() for slot in range(16) if slot != 7}
CALLS.update({
    "parent.vfn_7": model(_place, args=("r3", "r4", "r5", "r6")),
    0x82407C60: model(_transform, args=("r3", "r4"), deref={"r4": 24}),
    0x8240E6D0: stub(ret="void", args=("r3", "r4", "r5")),
})


def inputs(t):
    rng = t.rng
    command = t.alloc(0x30, "command")
    replacement = t.alloc(0x30, "postPlacementCommand")
    parent = t.alloc(0xE0, "parent")
    file = t.alloc(0x30, "currentFile")
    resources = t.alloc(8 * 4, "resources")
    t.w32(0x82602838, file)
    t.w32(file + 0x14, resources)
    for index in range(8):
        t.w32(resources + 4 * index, rng.choice((0, t.alloc(12, "definition"))))
    t.w32(parent, t.vtable("parent"))
    name = t.alloc(24, "parentName", fill=b"match HUD instance\0")
    t.w32(parent + 0xBC, name)
    t.w32(parent + 0xD4, command)
    t.w32(parent + 0xDC, replacement)

    def color(child):
        return rng.choice((0, child + 0x38, t.alloc(8, "color")))

    def child_storage(label):
        child = t.alloc(0xE0, label)
        t.w8(child + 0xAF, rng.choice((0, 2, 255)))
        t.w32(child + 0xD4, command)
        t.w32(child + 0xD8, color(child))
        return child

    created = child_storage("placedChild")
    t.w32(parent + 0xD8, rng.choice((0, created, created)))
    depths = sorted(rng.sample((0, 1, 255, 256, 32767, 32768, 65534, 65535), rng.randrange(7)))
    key = rng.choice(depths) if depths and rng.randrange(2) else rng.randrange(65536)
    head = 0
    selected = created
    for depth in reversed(depths):
        child = child_storage("existingChild")
        t.w16(child + 0xA6, depth)
        t.w32(child + 0xB8, head)
        head = child
        if depth == key:
            selected = child
    t.w32(parent + 0xB4, head)
    t.w16(command + 0x10, key)
    t.w16(command + 0x12, rng.choice((0, 1, 32768, 65535, rng.randrange(65536))))
    t.w16(command + 0x14, rng.choice((0xFFFF, 0xFFFF, rng.randrange(8))))
    t.w16(replacement + 0x10, rng.randrange(65536))

    for header in (command, replacement):
        t.w8(header + 5, rng.randrange(256))
        packed = t.alloc(12, "packedMatrix")
        for i in range(6):
            value = rng.choice((-32768, -32767, -257, -256, -1, 0, 1, 255, 256,
                                32767, rng.randrange(-32768, 32768)))
            t.w16(packed + 2 * i, value)
        t.w32(header + 0x18, rng.choice((0, packed, packed, packed)))
        t.w32(header + 0x1C, color(selected))
    t.args(r3=command, r4=parent)
