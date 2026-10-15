"""atHashMap<const char*>::Access (0x8234C208, atHashMap_Find): hash bucket walk, &value on a match."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "atHashMap_Find"
ADDRESS = 0x8234C208
SOURCE = "src/rage/data/at_types.cpp"

CALLS = {0x8223A818: run()}  # leaf; the original keeps r5/r6 live across it

NAMES = [b"Quality\0", b"Force\0", b"HitForce\0", b"Qual\0", b"\0"]


def inputs(t):
    rng = t.rng
    nb = rng.choice([0, 1, 3])
    m = t.alloc(8, "map")
    buckets = t.alloc(4 * max(nb, 1), "buckets", fill="zero")
    t.w32(m, buckets)
    t.w16(m + 4, nb)
    k = 0
    for b in range(nb):
        nxt = 0
        for _ in range(rng.choice([0, 1, 2, 3])):
            e = t.alloc(12, f"e{k}")
            t.w32(e, t.alloc(12, f"k{k}", fill=rng.choice(NAMES)))
            t.w32(e + 8, nxt)
            nxt = e
            k += 1
        t.w32(buckets + 4 * b, nxt)
    key = t.alloc(12, "key", fill=rng.choice(NAMES))
    t.args(r3=m, r4=key)
