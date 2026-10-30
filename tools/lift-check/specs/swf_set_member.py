"""SWF member update and pooled insertion, including lazy priority hashes.

The pool has a free node: the original dereferences its head before checking it.
Names are valid NUL-terminated ASCII strings; lookup and hashing run game code.
Hash equality, including collisions and case folding, determines member identity
and priority. No memory is ignored; the original has no meaningful return value.
"""
from liftcheck.spec import *

FUNCTION = "swfSetMember"
ADDRESS = 0x823FB258
SOURCE = "src/rage/swf_clip_events.cpp"
RET = None
CALLS = {0x823FB3B8: run(), 0x8223A868: run()}


def hash_name(name):
    h = 0
    for c in name.upper():
        h = (h * 16 + c) & 0xFFFFFFFF
        high = h & 0xF0000000
        h ^= high ^ (high >> 24)
    return h


def inputs(t):
    rng = t.rng
    names = [b"priority%d" % i for i in range(13)]
    ready = rng.choice((0, 1, 0xFF))
    for i, name in enumerate(names):
        t.w32(0x825C2D30 + 4 * i, t.alloc(len(name) + 1, "priorityName", fill=name + b"\0"))
        t.w32(0x82604CE8 + 4 * i, hash_name(name) if ready else t.u32())
    t.w8(0x826066C8, ready)

    scenario = rng.randrange(5)
    name = rng.choice(names).upper() if scenario in (2, 3) else b"ordinary_member"
    text = t.alloc(len(name) + 1, "name", fill=name + b"\0")
    value = t.alloc(8, "value")
    t.w32(value, t.u32())
    t.w32(value + 4, t.u32())
    pool = t.alloc(16, "pool")
    node = t.alloc(20, "freeNode")
    t.w32(node, t.alloc(20, "nextFree"))
    t.w32(pool + 12, node)
    t.w16(pool + 6, rng.choice((0, 1, 0xFFFF, rng.randrange(65536))))
    t.w32(0x82604C54, pool)

    member_list = t.alloc(8, "list")
    count = 0 if scenario == 0 else rng.randint(1, 4)
    nodes = [t.alloc(20, "existingNode") for _ in range(count)]
    for i, old in enumerate(nodes):
        t.w32(old + 12, nodes[i + 1] if i + 1 < count else 0)
        t.w32(old + 16, hash_name(name) if scenario == 1 and i == count - 1 else 0xDEADBEEF + i)
    t.w32(member_list, nodes[0] if nodes else 0)
    t.w32(member_list + 4, nodes[-1] if nodes else 0)
    t.args(r3=member_list, r4=text, r5=value)
