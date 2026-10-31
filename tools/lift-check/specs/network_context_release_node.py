"""0x823D2E00: reset one active node and append it to the free chain. Cover all
50 indices, empty/nonempty free tails, counter wrap and untouched node words.
The index is derived from the shared typed array; no guest-sized host stride.
"""
from liftcheck.spec import *
FUNCTION = "networkContextReleaseNode"
ADDRESS = 0x823D2E00
SOURCE = "src/game/network/network_context.cpp"
TRIALS = 1000


def inputs(t):
    r = t.rng
    pool = t.alloc(0x6D0, 'pool', ctype='NetworkContextPool')
    index = r.randrange(50)
    tail = r.choice([0xFFFF] + [i for i in range(50) if i != index])
    t.w16(pool + 0x4B0, r.choice([0, 1, 49, 0xFFFF, r.randrange(65536)]))
    t.w16(pool + 0x4B4, tail)
    t.w32(pool + 0x4C8, r.choice([0, 1, 50, 0xFFFFFFFF, t.u32()]))
    t.args(r3=pool, r4=pool + index * 24)
