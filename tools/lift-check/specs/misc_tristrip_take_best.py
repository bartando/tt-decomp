"""TriStripList::TakeBest: replays candidate strips on copies of the vertex cache
(StripVertexCache::Access runs as the original on both sides), reverses the
winner if backwards scored higher and swaps it into slot 0."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "TriStripList::TakeBest"
ADDRESS = 0x82134C10
SOURCE = "src/game/misc/cm_operators.cpp"

CALLS = {
    0x821357B8: run(),      # StripVertexCache::Access
}


def fill_cache(t, cache, pool):
    rng = t.rng
    t.w32(cache + 0x00, rng.randrange(1000))
    for k in range(18):
        empty = rng.random() < 0.2
        t.w16(cache + 0x04 + 2 * k, 0xFFFF if empty else rng.choice(pool))
        t.w32(cache + 0x28 + 4 * k, rng.choice([0, 1, 2, 2]))
        t.w8(cache + 0x74 + k, rng.choice([0, 1]))
    t.w32(cache + 0x70, rng.randrange(18))


def make_strips(t, n, pool):
    rng = t.rng
    items = t.alloc(4 * max(n, 1), "items")
    for k in range(n):
        s = t.alloc(0x18, f"strip{k}")
        m = rng.randrange(1, 14)
        idx = t.alloc(2 * m, f"strip{k}.indices")
        for j in range(m):
            t.w16(idx + 2 * j, rng.choice(pool))
        t.w32(s + 0x00, rng.choice([0, 1]))
        t.w32(s + 0x04, m)
        t.w32(s + 0x0C, m)
        t.w32(s + 0x10, idx)
        t.w32(items + 4 * k, s)
    return items


def inputs(t):
    rng = t.rng
    pool = [rng.randrange(0x10000) for _ in range(rng.choice([6, 12, 30]))]
    n = rng.choice([0, 1, 2, 4, 7])
    lst = t.alloc(8, "list", fill="zero")
    t.w32(lst, make_strips(t, n, pool))
    t.w32(lst + 4, n)
    cache = t.alloc(0x88, "cache", fill="zero")
    fill_cache(t, cache, pool)
    t.args(r3=lst, r4=cache)
