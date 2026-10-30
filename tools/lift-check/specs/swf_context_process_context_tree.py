"""Context tree dispatch, stack bookkeeping, and recursive traversal.

Limits: virtual methods are models, not their real implementations. Trees are
finite and acyclic; callbacks may change a node's child/sibling links and focus
but do not free nodes. The stack count is restricted to 0..33 (negative values
would write before the stack). No memory is ignored.
"""
import struct
from liftcheck.spec import *

FUNCTION = "rage::swfCONTEXT_ProcessContextTree"
ADDRESS = 0x823FCA50
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000


def u32(c, addr):
    return int.from_bytes(c.read(addr, 4), "big")


def probe(c):
    obj = c.r(3)
    c.ret(r3=u32(c, obj + 4))
    if u32(c, obj + 32):
        c.write(u32(c, obj + 8) + 184, b"\0" * 4)
    # Dispatch can change the first child before traversal.
    node = u32(c, obj + 8)
    if u32(c, obj + 12):
        c.write(node + 180, c.read(obj + 16, 4))


def transition(c):
    obj, node = c.r(3), c.r(4)
    assert (c.r(5), c.r(6)) == (2, 1)
    c.write(obj + 20, struct.pack(">I", u32(c, obj + 20) + 1))
    # The caller clears focus even if the callback changes it.
    if u32(c, obj + 24):
        c.write(0x8260281C, struct.pack(">I", u32(c, obj + 24)))
    if u32(c, obj + 28):
        c.write(node + 180, c.read(obj + 16, 4))


CALLS = {
    "definition.vfn_6": model(probe, args=("r3",)),
    "definition.vfn_3": model(transition, args=("r3", "r4", "r5", "r6")),
}


def inputs(t):
    r = t.rng
    nodes = [t.alloc(188, f"node{i}", fill="zero") for i in range(r.choice((1, 2, 3, 5, 7)))]
    table = t.vtable("definition")
    for i, node in enumerate(nodes):
        obj = t.alloc(36, f"definition{i}", fill="zero")
        t.w32(obj, table)
        t.w32(obj + 4, r.choice((0, 1, 2, 0x100, 0x101, 0xFFFFFFFF)))
        t.w32(obj + 8, node)
        t.w32(node + 4, obj)
        t.w8(node + 173, r.choice((0, 1, 2, 255)))
        nested = t.alloc(171, f"nested{i}", fill="zero")
        t.w8(nested + 170, r.choice((0, 1, 255)))
        t.w32(node + 176, r.choice((0, nested)))
        t.w32(obj + 24, r.choice((0, *nodes)))
        t.w32(obj + 12, r.randrange(5) == 0)
        t.w32(obj + 28, r.randrange(5) == 0)
        t.w32(obj + 32, r.randrange(8) == 0)
    # Acyclic tree, with sibling chains and nested descendants.
    last = {}
    for i in range(1, len(nodes)):
        parent = r.randrange(i)
        t.w32(nodes[last[parent]] + 184 if parent in last else nodes[parent] + 180, nodes[i])
        last[parent] = i
    t.w32(0x8260281C, r.choice((0, *nodes)))
    t.w32(0x8260484C, r.choice((0, 1, 30, 31, 32, 33)))
    t.w32(0x82604C64, r.getrandbits(32))
    t.args(r3=nodes[0])
