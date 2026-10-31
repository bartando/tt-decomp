"""0x823D2BE8: drain the active chain through the real release helper, then reset
counts and indices. Check empty/single/multiple/full pools, varied chain order,
existing free nodes, preserved payload words and underflowing active counts.
"""
from liftcheck.spec import *
FUNCTION = "UpdateNetworkState"
ADDRESS = 0x823D2BE8
SOURCE = "src/game/network/network_context.cpp"
TRIALS = 1000
CALLS = {"networkContextReleaseNode": run(transparent=True, args=("r3", "r4"))}


def inputs(t):
    r = t.rng
    pool = t.alloc(0x6D0, 'pool', ctype='NetworkContextPool')
    indices = list(range(50))
    r.shuffle(indices)
    count = r.choice([0, 1, 2, 10, 49, 50])
    active, free = indices[:count], indices[count:]
    for i, index in enumerate(active):
        t.w32(pool + index * 24 + 16,
              pool + active[i + 1] * 24 if i + 1 < count else 0)
    for i, index in enumerate(free):
        t.w16(pool + index * 24 + 20, free[i + 1] if i + 1 < len(free) else 0xFFFF)
        t.w16(pool + index * 24 + 22, free[i - 1] if i else 0xFFFF)
    t.w16(pool + 0x4B0, len(free))
    t.w16(pool + 0x4B4, free[0] if free else 0xFFFF)
    t.w32(pool + 0x4C0, pool + active[0] * 24 if active else 0)
    t.w32(pool + 0x4C8, r.choice([count, 0, 0xFFFFFFFF]))
    t.args(r3=pool)
