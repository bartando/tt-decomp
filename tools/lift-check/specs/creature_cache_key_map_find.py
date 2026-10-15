"""CacheKeyMap::Find (0x82121660): Jenkins integer hash, chained buckets."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "CacheKeyMap::Find"
ADDRESS = 0x82121660
SOURCE = "src/game/creature/pong_creature.cpp"


def jenkins(h):
    for s, add in ((12, 1), (22, 0), (4, 1), (9, 0), (10, 1), (2, 0), (7, 1), (12, 0)):
        h = (h + (h << s)) & 0xFFFFFFFF if add else h ^ (h >> s)
    return h or 1


def inputs(t):
    rng = t.rng
    nb = rng.choice([1, 4, 16])
    keys = [rng.getrandbits(32) for _ in range(rng.choice([0, 3, 12]))]
    buckets = t.alloc(4 * nb, "buckets", fill="zero")
    heads = [0] * nb
    for k in keys:
        b = jenkins(k) & (nb - 1)
        node = t.alloc(0x10, "node")
        t.w32(node, k)
        t.w16(node + 4, rng.randrange(5))
        t.w32(node + 8, heads[b])
        heads[b] = node
    for b, h in enumerate(heads):
        t.w32(buckets + 4 * b, h)
    m = t.alloc(0x10, "map")
    t.w32(m, nb)
    t.w32(m + 4, len(keys))
    t.w32(m + 8, buckets)
    probe = t.alloc(8, "probe")
    t.w32(probe, rng.choice(keys + [rng.getrandbits(32), 0]) if keys else rng.getrandbits(32))
    t.args(r3=m, r4=probe)
