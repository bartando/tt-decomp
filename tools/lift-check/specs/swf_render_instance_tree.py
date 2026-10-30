"""Recursive SWF rendering: transforms, colour, mask depth, callbacks and draws.

Limits: valid aligned instances/parent transforms and finite acyclic trees only;
callbacks may change render state, alpha, transforms and sibling links but do
not free nodes. Matrix concat, colour concat and transform rebuild run original
code on both sides (sin/cos use libm models). GPU clear/bind/flush, callbacks and
leaf draws are boundary models; the slot-13 mode query returns a scripted bool.
This checks those boundaries' arguments and effects,
not GPU output or a live match. No ignored memory or float tolerance. NaN payloads
and zero signs are subject to lift-check's normal float comparison rules; the
translation-cache flag independently checks unordered/equal branch behavior.
"""
import math
import struct
from liftcheck.spec import *

FUNCTION = "rage::swfRenderInstanceTree"
ADDRESS = 0x823FD450
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
RET = None

FLAGS = 0x825EBB1C
APPLIED = 0x825EBB80
PENDING = 0x825EBBD8
MASK_END = 0x826066CC
OWNER = 0x82602814


def u32(c, address):
    return int.from_bytes(c.read(address, 4), "big")


def w32(c, address, value):
    c.write(address, struct.pack(">I", value & 0xFFFFFFFF))


def render_state(c):
    # Transient dirty bits can be repaired by mask cleanup before the function
    # returns. Record the state visible to rendering/callbacks as well.
    return (c.read(FLAGS, 4) + c.read(PENDING + 24, 4) +
            c.read(PENDING + 36, 4) + c.read(MASK_END, 2))


def texture(c):
    assert c.r(3) == c.r(4) == 0
    # A bind can dirty the state, requiring the following flush.
    w32(c, FLAGS, u32(c, FLAGS) ^ u32(c, c.r(5)))


def flush(c):
    c.write(APPLIED, c.read(PENDING, 88))
    w32(c, FLAGS, 0)
    w32(c, 0x825EBAB4, 0)


def clear(c):
    assert tuple(c.r(n) for n in range(3, 8)) == (0, 0, 1, 0, 0)
    assert c.f(1) == 1.0
    # GPU clear can also update the shared state before the mask setup.
    w32(c, FLAGS, u32(c, FLAGS) ^ 0x2A5)


def callback(c):
    node = c.r(4) - 0x98
    owner = u32(c, OWNER)
    assert c.r(3) == owner + 4
    c.write(owner + 36, render_state(c))
    w32(c, FLAGS, u32(c, owner + 20))
    w32(c, APPLIED + 24, u32(c, owner + 24))
    w32(c, PENDING + 24, u32(c, owner + 28))
    # Callback flags explicitly exercise the second alpha check and the late
    # reads of the blend/mask flags.
    changes = u32(c, owner + 32)
    if changes & 1:
        c.write(node + 0x43, bytes([0]))
    if changes & 2:
        c.write(node + 0x9C, bytes([1]))
    if changes & 4:
        c.write(node + 0xA8, bytes(2))


def draw(c):
    definition, transform, mode = c.r(3), c.r(4), c.r(5)
    node = transform - 8
    assert u32(c, node + 4) == definition
    assert mode in (1, 2, 3)
    c.write(definition + 32, render_state(c))
    changes = u32(c, definition + 4)
    if changes & 1:
        w32(c, FLAGS, u32(c, definition + 8))
        w32(c, APPLIED + 24, u32(c, definition + 12))
        w32(c, APPLIED + 36, u32(c, definition + 16))
    if changes & 2:
        c.write(node + 0x43, bytes([64]))
    if changes & 4:
        c.write(node + 0x30, c.read(definition + 20, 8))
    if changes & 8:
        c.write(node + 0xB8, c.read(definition + 28, 4))


CALLS = {
    0x823FB018: run(),
    0x823FA2A0: run(),
    0x823FA1E0: run(),
    0x823FAE98: run(),
    0x824302B0: model(lambda c: c.ret(f1=math.cos(c.f(1))) if math.isfinite(c.f(1))
                     else c.ret(f1=float("nan")), args=("f1",)),
    0x824301D8: model(lambda c: c.ret(f1=math.sin(c.f(1))) if math.isfinite(c.f(1))
                     else c.ret(f1=float("nan")), args=("f1",)),
    0x820F76F8: model(texture, args=("r3", "r4", "r5")),
    0x8215B138: model(flush, args=()),
    0x8214F088: model(clear, args=("r3", "r4", "r5", "r6", "r7", "f1")),
    0x8225FFF8: model(callback, args=("r3", "r4"), deref={"r4": 4}),
    # r3=13 at this call site is dead: the callee loads slot 13 itself.
    0x823FB1F0: stub(ret=lambda c: c.rng.randrange(2), args=()),
    "definition.vfn_1": model(draw, args=("r3", "r4", "r5"), deref={"r4": 144}),
}
CALLS[0x823FA1E0].deref = {"r4": 24, "r5": 24}
CALLS[0x823FAE98].deref = {"r4": 8, "r5": 8}

SPECIAL = (0, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC00000,
           1, 0x80000001, 0x7F7FFFFF)


def inputs(t):
    r = t.rng
    parent = t.alloc(144, "parentTransform")
    t.floats(parent, 12, -20, 20)
    for offset in (56, 57, 58):
        t.w8(parent + offset, r.randrange(256))
    t.w8(parent + 59, 64)
    for offset in (60, 61, 62, 63):
        t.w8(parent + offset, r.randrange(256))
    for offset in (68, 69, 70):
        t.w8(parent + offset, r.randrange(256))
    t.w8(parent + 71, 255)
    t.w8(parent + 140, r.choice((0, 1, 127, 255)))

    nodes = [t.alloc(0xD4, f"node{i}") for i in range(r.choice((1, 1, 1, 2, 4, 7)))]
    table = t.vtable("definition", slots=2)
    parents = [None] + [r.randrange(i) for i in range(1, len(nodes))]
    last_child = {}
    definitions = []
    depth_values = []
    for i, node in enumerate(nodes):
        definition = t.alloc(48, f"definition{i}")
        definitions.append(definition)
        t.w32(definition, table)
        t.w32(definition + 4, r.randrange(16))
        t.w32(definition + 8, r.getrandbits(32))
        t.w32(definition + 12, r.choice((0, 2, 3, 5)))
        t.w32(definition + 16, r.choice((0, 1, 15)))
        t.floats(definition + 20, 2, -100, 100)
        t.w32(definition + 28, 0)
        t.w32(node + 4, definition)
        t.floats(node + 8, 35, -50, 50)
        # Valid scale defaults in the embedded transform's rebuild state.
        t.wf32(node + 0x60, 100.0)
        t.wf32(node + 0x64, 100.0)
        t.wf32(node + 0x68, 100.0)
        t.wf32(node + 0x6C, 100.0)
        t.wf32(node + 0x54, 0.0)
        t.w8(node + 0x95, r.choice((0, 0, 0, 1, 255)))
        t.w8(node + 0xAF, r.choice((0, 1, 1, 1, 1, 255)))
        t.w8(node + 0x9C, r.choice((0, 0, 1, 255)))
        t.w32(node + 0x98, r.choice((0, 1, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF)))
        t.w16(node + 0xA8, r.choice((0, 0, 0, 1, 2, 65535)))
        depth = r.choice((0, 1, 2, 32768, 65534, 65535, r.randrange(65536)))
        depth_values.append(depth)
        t.w16(node + 0xA6, depth)
        t.w32(node + 0xB0, 0 if parents[i] is None else nodes[parents[i]])
        t.w32(node + 0xB4, 0)
        t.w32(node + 0xB8, 0)
        if parents[i] is not None:
            p = parents[i]
            t.w32(nodes[last_child[p]] + 0xB8 if p in last_child else nodes[p] + 0xB4, node)
            last_child[p] = i
        texture_ptr = t.alloc(4, f"texture{i}")
        t.w32(texture_ptr, r.choice((0, 0x40, 0x200, r.getrandbits(32))))
        t.w32(node + 0x90, r.choice((0, 0, texture_ptr)))
        # Colour helper runs, so alpha comes from the actual inherited colour.
        for offset in range(0x38, 0x3B):
            t.w8(node + offset, r.randrange(256))
        for offset in range(0x3C, 0x40):
            t.w8(node + offset, 0)
        for offset in range(0x4C, 0x4F):
            t.w8(node + offset, r.randrange(256))
        t.w8(node + 0x4F, 255)
        t.w8(node + 0x3B, r.choice((0, 1, 64, 64, 127, 128, 255)))

    # The root can have ancestors outside the rendered subtree; exercise depth
    # overflow and exact end-depth equality without introducing cycles.
    ancestor = 0
    root_depth = depth_values[0]
    for i in range(r.randrange(4)):
        a = t.alloc(0xB4, f"ancestor{i}")
        depth = r.choice((0, 1, 32768, 65535))
        t.w16(a + 0xA6, depth)
        root_depth = (root_depth + depth) & 65535
        t.w32(a + 0xB0, ancestor)
        ancestor = a
    t.w32(nodes[0] + 0xB0, ancestor)

    # Single-leaf cases force stable/moved/NaN/signed-zero translations. These
    # distinguish the cache flag from a mere byte comparison or ordered test.
    if len(nodes) == 1 and r.randrange(2):
        node = nodes[0]
        for base in (node + 8, parent + 24):
            for k, value in enumerate((1, 0, 0, 1, 0, 0)):
                t.wf32(base + 4 * k, value)
        for k in (4, 5):
            t.w32(node + 0x20 + 4 * k, r.choice((0, 0x80000000, 0x3F800000, 0x7FC00000)))
        t.w8(node + 0xAF, 1)
        t.w8(node + 0x95, 0)
        t.w8(node + 0x3B, 64)
        t.w32(node + 0x98, 0xFFFFFFFF)
        t.w32(definitions[0] + 4, 0)
    elif r.randrange(4) == 0:
        for base in (nodes[0] + 8, parent + 24):
            t.w32(base + r.randrange(6) * 4, r.choice(SPECIAL))

    owner = t.alloc(52, "callbackOwner")
    t.w32(owner + 16, r.choice((0, 0, 1, 0xFFFFFFFF)))
    t.w32(owner + 20, r.getrandbits(32))
    t.w32(owner + 24, r.choice((0, 2, 3, 5)))
    t.w32(owner + 28, r.choice((0, 2, 3, 5)))
    t.w32(owner + 32, r.randrange(8))
    t.w32(OWNER, owner)
    t.w32(0x8260281C, r.choice((0, *nodes)))
    t.w32(FLAGS, r.choice((0, 0, 0x40, 0x200, 0x240, r.getrandbits(32))))
    t.w32(0x825EBAB4, r.choice((0, 0, 1)))
    for base in (APPLIED, PENDING):
        for k in range(22):
            t.w32(base + 4 * k, r.getrandbits(32))
        t.w32(base + 24, r.choice((0, 1, 2, 3, 5)))
        t.w32(base + 36, r.choice((0, 1, 15)))
    t.w16(MASK_END, r.choice((0, 0, 1, root_depth, (root_depth - 1) & 65535, 65535)))
    t.args(r3=nodes[0], r4=parent)
