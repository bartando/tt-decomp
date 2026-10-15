"""xactGlobalVariable::Dtor: returns every listener node to the free list,
clears tail and count, frees the extra chunks (0x8244EA00, stubbed) and drops
to the base vtable."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "xactGlobalVariable::Dtor"
ADDRESS = 0x8244B2A8
SOURCE = "src/game/network/msg_msg_sink.cpp"
EXTERNS = {"xactPtrList::FreeChunks": 0x8244EA00}

CALLS = {
    0x8244EA00: stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    var = t.alloc(0xFC, "variable")
    lst = var + 0x18
    n = rng.choice([0, 1, 2, 5])
    nodes = [t.alloc(0xC, f"node{k}") for k in range(n)]
    for k, node in enumerate(nodes):
        t.w32(node + 4, nodes[k + 1] if k + 1 < n else 0)
    t.w32(lst + 0xCC, nodes[0] if n else 0)
    t.w32(lst + 0x00, t.alloc(0xC, "freeNode") if rng.random() < 0.5 else 0)
    t.args(r3=var)
