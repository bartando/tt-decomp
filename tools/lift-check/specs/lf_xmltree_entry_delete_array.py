"""xmlTreeEntry delete[] (0x820C2980): destructs entries back to front, frees the counted block."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "xmlTreeEntry_DeleteArray"
ADDRESS = 0x820C2980
SOURCE = "src/rage/data/at_types.cpp"

CALLS = {
    0x821A8118: stub(ret="void"),
    0x820C00C0: stub(ret="void"),
}


def inputs(t):
    n = t.rng.choice([0, 1, 2, 5])
    block = t.alloc(4 + 12 * max(n, 1), "block")
    t.w32(block, n)
    t.args(r3=block + 4, r4=t.u32())
