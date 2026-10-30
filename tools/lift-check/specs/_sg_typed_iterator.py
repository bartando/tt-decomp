"""Finite trees with scripted type checks; all links and call arguments observable."""
import struct
from liftcheck.spec import model, run, stub


def type_check(ctx):
    node = ctx.r(3)
    result, iterator, replacement = struct.unpack(">III", ctx.read(node + 16, 12))
    if iterator:
        ctx.write(iterator + 4, struct.pack(">I", replacement))
    ctx.ret(r3=result)


def node_name(ctx):
    ctx.ret(r3=struct.unpack(">I", ctx.read(ctx.r(3) + 28, 4))[0])


CALLS = {
    "node.vfn_20": model(type_check, args=("r3", "r4"), deref={"r3": 16}),
    "node.vfn_19": model(node_name, args=("r3",)),
    "nop_8240E6D0": stub(ret="void", args=("r3", "r4")),
    0x823DA070: run(args=("r3",), deref={"r3": 8}),
    0x823D9FD0: run(args=("r3",), deref={"r3": 8}),
    0x823DA0F8: run(args=("r3", "r4"), deref={"r3": 8, "r4": 16}),
}


def inputs(t):
    rng = t.rng
    iterator = t.alloc(8, "iterator")
    vt = t.vtable("node", 24)
    nodes = [t.alloc(32, f"node {i}") for i in range(18)]
    parents = [-1]
    children = [[] for _ in nodes]
    # Chains force climbs past several ancestors; random trees add siblings.
    chain = rng.randrange(3) == 0
    for i in range(1, len(nodes)):
        parent = i - 1 if chain else rng.randrange(i)
        parents.append(parent)
        children[parent].append(i)
    name = t.alloc(32, "debug name", fill=b"iterator-spec-node\0")
    replacement = t.alloc(32, "callback replacement leaf", fill="zero")
    t.w32(replacement, vt)
    t.w32(replacement + 16, 1)
    t.w32(replacement + 28, t.alloc(32, "replacement name", fill=b"replacement-node\0"))
    for i, node in enumerate(nodes):
        siblings = children[parents[i]] if i else [0]
        pos = siblings.index(i)
        sibling = nodes[siblings[pos + 1]] if pos + 1 < len(siblings) else 0
        t.w32(node, vt)
        t.w32(node + 4, nodes[parents[i]] if i else 0)
        t.w32(node + 8, sibling)
        t.w32(node + 12, nodes[children[i][0]] if children[i] else 0)
        t.w32(node + 16, rng.choice([0, 0, 1, 2, 0x80, 0xff, 0x100, 0x12340000]))
        t.w32(node + 20, 0)
        t.w32(node + 24, 0)
        t.w32(node + 28, name)
    root_index = rng.choice([0, 0, 0, rng.randrange(len(nodes))])
    descendants = []

    def visit(i):
        descendants.append(i)
        for child in children[i]:
            visit(child)

    visit(root_index)
    current_index = rng.choice(descendants)
    current = rng.choice([0, nodes[current_index], nodes[current_index]])
    t.w32(iterator, nodes[root_index])
    t.w32(iterator + 4, current)
    # IsType may change the cursor. Prime must reload before fetching its name.
    if current and rng.randrange(5) == 0:
        t.w32(current + 16, rng.choice([0, 0x100, 0x80000000]))
        t.w32(current + 20, iterator)
        # An independent leaf avoids callback-created traversal cycles.
        t.w32(current + 24, replacement)
    # Also cover an orphan below a non-null boundary.
    if current and rng.randrange(8) == 0:
        t.w32(current + 4, 0)
        t.w32(current + 8, 0)
        t.w32(current + 12, 0)
    t.w32(0x825C93D0, rng.getrandbits(32))
    t.args(r3=iterator)
