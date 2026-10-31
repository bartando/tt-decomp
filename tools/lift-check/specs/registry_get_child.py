"""Registry child lookup: empty, first/interior/last, out-of-range and signed keys."""
from liftcheck.spec import *

FUNCTION = "pg_C2A0_g"
ADDRESS = 0x821DC2A0
SOURCE = "src/rage/core/indexed_registry.cpp"
TRIALS = 600


def inputs(t):
    rng = t.rng
    root = t.alloc(0x10, "registry")
    children = t.alloc(0x10, "children")
    t.w32(root + 8, children)
    n = rng.choice([0, 1, 2, 3, 8, 31])
    nodes = [t.alloc(0x20, f"node{i}") for i in range(n)]
    for i, node in enumerate(nodes):
        t.w32(node + 8, nodes[i + 1] if i + 1 < n else 0)
    t.w32(children + 0xC, nodes[0] if n else 0)
    key = rng.choice([0, 1, max(0, n - 1), n, n + 1, 0xFFFFFFFF, 0x80000000])
    t.args(r3=root, r4=key)
