"""StripVertexCache::Access: integer logic over an 18-slot FIFO vertex cache."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "StripVertexCache::Access"
ADDRESS = 0x821357B8
SOURCE = "src/game/misc/cm_operators.cpp"


def inputs(t):
    rng = t.rng
    cache = t.alloc(0x88, "cache", fill="zero")
    vertex_pool = [rng.randrange(0x10000) for _ in range(rng.choice([4, 12, 30]))]
    t.w32(cache + 0x00, rng.randrange(1000))                      # m_hits
    for k in range(18):
        empty = rng.random() < 0.2
        t.w16(cache + 0x04 + 2 * k, 0xFFFF if empty else rng.choice(vertex_pool))
        t.w32(cache + 0x28 + 4 * k, rng.choice([0, 1, 2, rng.getrandbits(32)]))
        t.w8(cache + 0x74 + k, rng.choice([0, 1]))
    t.w32(cache + 0x70, rng.randrange(18))                        # m_next
    pass_ = rng.choice([1, 2, rng.getrandbits(32)])
    vertex = rng.choice(vertex_pool + [0xFFFF, rng.randrange(0x10000)])
    t.args(r3=cache, r4=pass_, r5=vertex)
