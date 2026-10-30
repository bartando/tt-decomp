"""SWF clip-event list rebuild: release old nodes to the pool, take one per record.

The pool always has enough free nodes (an empty pool faults on both sides: the
original reads the head's link before its null test). Covers empty and long old
lists, count <= 0, null records and a 16-bit free count near its wrap.
"""
from liftcheck.spec import *

FUNCTION = "swfSetClipEvents"
ADDRESS = 0x823FD320
SOURCE = "src/rage/swf_clip_events.cpp"
RET = None

POOL_GLOBAL = 0x82604C5C


def inputs(t):
    rng = t.rng
    pool = t.alloc(0x10, "pool")
    nodes = t.alloc(8 * 64, "nodes")
    count = rng.choice([0, -1, 1, 2, 5, rng.randint(1, 24)])
    free = rng.randint(max(count, 0), 40)
    head = 0
    for k in range(free):
        node = nodes + 8 * k
        t.w32(node, head)
        t.w32(node + 4, t.u32())
        head = node
    t.w32(pool + 0x0C, head)
    t.w16(pool + 0x06, rng.choice([free, 0xFFFF, 0, rng.randrange(65536)]))
    t.w32(POOL_GLOBAL, pool)

    inst = t.alloc(0xD0, "instance")
    old = 0
    for k in range(rng.choice([0, 0, 1, 3, rng.randint(0, 20)])):
        node = nodes + 8 * (40 + k)
        t.w32(node, t.u32())
        t.w32(node + 4, old)
        old = node
    t.w32(inst + 0xC8, old)
    t.w32(inst + 0xC4, t.u32())
    records = rng.choice([0, t.alloc(12 * 24, "records")])
    t.args(r3=inst, r4=t.u32(), r5=records, r6=count & 0xFFFFFFFF)
