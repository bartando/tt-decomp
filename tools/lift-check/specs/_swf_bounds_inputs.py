"""Bounds trees with a defined minimum for every child subtree.

Empty roots exercise the no-write contract. Empty descendant subtrees are
excluded: retail consumes uninitialized stack bytes when such a child returns.
Definition callbacks remain a boundary and return a supplied rectangle or null.
"""
from liftcheck.spec import *


def bounds(c):
    c.ret(r3=int.from_bytes(c.read(c.r(3) + 4, 4), "big"))


CALLS = {"definition.vfn_9": model(bounds, args=("r3",)), 0x823FEF98: run()}


def inputs(t):
    rng = t.rng
    mode = t.index % 5

    def node(depth, must_have_bounds):
        obj = t.alloc(0xBC, "instance")
        definition = t.alloc(8, "definition")
        t.w32(definition, t.vtable("definition", slots=10))
        t.w32(obj + 4, definition)
        # Most nodes are rectangles. Container-only roots exercise aggregation.
        rect = t.alloc(16, "bounds") if must_have_bounds or rng.randrange(2) else 0
        t.w32(definition + 4, rect)
        if rect:
            for i in range(4):
                t.w32(rect + i * 4, rng.choice((0, 1, 0xffffffff, 0x7fffffff,
                                               0x80000000, rng.getrandbits(32))))
        count = rng.randrange(1, 4) if depth > 0 else 0
        head = 0
        for _ in range(count):
            child = node(depth - 1, True)
            t.w32(child + 0xB8, head)
            head = child
        t.w32(obj + 0xB4, head)
        t.w32(obj + 0xB8, 0)
        return obj

    root = node(0 if mode == 0 else rng.randrange(3), mode != 0)
    if mode == 1:
        # Null root rectangle with nonempty children.
        definition = t.alloc(8, "containerDefinition")
        t.w32(definition, t.vtable("definition", slots=10))
        t.w32(definition + 4, 0)
        t.w32(root + 4, definition)
    out = t.alloc(4, "minimum", ctype=None) if rng.randrange(2) else 0
    if out:
        t.wf32(out, rng.uniform(-1000, 1000))
    t.args(r3=root, r4=out)
