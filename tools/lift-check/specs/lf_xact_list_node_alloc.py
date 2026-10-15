"""XACT list node pool (0x8244BDE0): pop the free list, carving a 16-node chunk when empty."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "xactListNodePool_Alloc"
ADDRESS = 0x8244BDE0
SOURCE = "src/rage/core/rage_core_utils.cpp"

CALLS = {0x820C01B8: model(lambda c: c.ret(r3=c.alloc(0xC4) if c.rng.random() < 0.8 else 0))}


def inputs(t):
    pool = t.alloc(8, "pool")
    free = 0
    for i in range(t.rng.choice([0, 0, 1, 2])):
        n = t.alloc(12, f"free{i}")
        t.w32(n + 4, free)
        free = n
    t.w32(pool, free)
    t.args(r3=pool)
