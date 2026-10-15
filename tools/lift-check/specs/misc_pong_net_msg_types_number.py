"""pongNetMessageHolder_8B80_w: flattens the registered message-type list,
qsorts it (the CRT qsort and its comparator run as the original on both sides)
and numbers the first registeredCount entries."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongNetMessageHolder_8B80_w"
ADDRESS = 0x82238B80
SOURCE = "src/game/network/pong_network.cpp"

OWNER = {}

CALLS = {
    0x82238D60: stub(ret=lambda ctx: OWNER["addr"]),   # xam_singleton_init_8D60
    0x820DEC88: alloc(size_reg="r3"),                  # xe_EC88
    0x82431950: run(),                                  # qsort
    0x82238F28: run(),                                  # its comparator
}


def inputs(t):
    rng = t.rng
    owner = t.alloc(0x18, "owner", fill="zero")
    OWNER["addr"] = owner
    n = rng.choice([0, 1, 2, 5, 9])
    names = [b"ball", b"hit", b"serve", b"accept", b"drop", b"zz", b"a", b"score", b"pause"]
    head = 0
    nodes = []
    for k in range(n):
        node = t.alloc(0xC, f"node{k}")
        nm = t.alloc(16, f"name{k}", fill=rng.choice(names) + b"\0")
        t.w32(node, 0xFFFFFFFF if rng.random() < 0.6 else rng.randrange(50))
        t.w32(node + 4, nm)
        t.w32(node + 8, head)
        head = node
        nodes.append(node)
    t.w32(owner + 8, head)
    t.w16(owner + 4, 0 if rng.random() < 0.85 else rng.randrange(1, 5))
    cap = 0 if rng.random() < 0.7 else n + rng.randrange(3)
    t.w16(owner + 6, cap)
    if cap:
        t.w32(owner, t.alloc(4 * cap, "arr"))
    t.w32(owner + 12, rng.randrange(0, n + 1))
    t.w32(owner + 16, rng.choice([0, 1, 100, -5]))
