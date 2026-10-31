"""0x82134350: erase by slot address, free a strip's two arrays and the strip,
then close the gap. Covers empty lists, null slots, first/interior/last matches,
strip-address and unrelated-pointer misses, with all writes/calls compared."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "TriStripList::Erase"
ADDRESS = 0x82134350
SOURCE = "src/graphics/tri_strip_list.cpp"
TRIALS = 1000
CALLS = {"rage_free": stub(ret="void", args=("r3",))}


def inputs(t):
    rng = t.rng
    n = rng.choice([0, 1, 2, 5, 9])
    lst = t.alloc(8, "list", fill="zero")
    items = t.alloc(4 * max(n, 1) + 4, "items")
    strips = []
    for k in range(n):
        s = t.alloc(0x18, f"strip{k}")
        strips.append(s)
        t.w32(items + 4 * k, 0 if rng.random() < 0.1 else s)
    t.w32(lst, items)
    t.w32(lst + 4, n)
    k = rng.randrange(max(n, 1))
    target = rng.choice([items + 4 * k, items + 4 * k, items + 4 * k,
                         strips[k] if n else 0, rng.getrandbits(32)])
    t.args(r3=lst, r4=target)
