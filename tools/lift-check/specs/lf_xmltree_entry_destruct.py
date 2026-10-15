"""xmlTreeEntry destructor (0x821A8118): deletes the node list, frees the name."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "xmlTreeEntry_Destruct"
ADDRESS = 0x821A8118
SOURCE = "src/rage/data/at_types.cpp"

CALLS = {
    0x820C00C0: stub(ret="void"),
    **{f"node{i}.vfn_0": stub(ret="void", args=("r3", "r4")) for i in range(3)},
}


def inputs(t):
    entry = t.alloc(12, "entry")
    nxt = 0
    for i in range(t.rng.choice([0, 1, 3])):
        node = t.alloc(12, f"node{i}")
        t.w32(node, t.vtable(f"node{i}"))
        t.w32(node + 8, nxt)
        nxt = node
    t.w32(entry + 8, nxt)
    t.args(r3=entry)
