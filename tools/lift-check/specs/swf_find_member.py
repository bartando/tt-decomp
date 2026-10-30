"""Finite member chains: empty/missing, every hit position and first collision.

Run the original case-insensitive hash, including signed high-byte characters.
Node names deliberately differ from the queried name: equality is hash-only.
Unrelated payload/tag words and the list's tail are dirty. No ignored memory.
"""
from liftcheck.spec import *

FUNCTION = "swfFindMember"
ADDRESS = 0x823FB3B8
SOURCE = "src/rage/swf.cpp"
TRIALS = 1200
CALLS = {0x8223A868: run()}


def hash_name(text):
    h = 0
    for ch in text:
        ch = ch - 256 if ch >= 128 else ch
        if 97 <= ch <= 122:
            ch -= 32
        h = ((h << 4) + ch) & 0xFFFFFFFF
        high = h & 0xF0000000
        h ^= high ^ (high >> 24)
    return h


def inputs(t):
    r = t.rng
    scenario = t.index % 7
    text = r.choice((b"", b"onEnterFrame", b"ONenterFRAME", b"priority12", b"a" * 127,
                     bytes(r.randrange(1, 256) for _ in range(r.randrange(1, 60)))))
    name = t.alloc(len(text) + 1, "name", fill=text + b"\0")
    h = hash_name(text)
    count = 0 if scenario == 0 else r.randrange(2, 10)
    nodes = [t.alloc(20, "memberNode") for _ in range(count)]
    hit = {2: 0, 3: count // 2, 4: count - 1, 5: 0, 6: count // 2}.get(scenario, -1)
    for i, node in enumerate(nodes):
        t.w32(node, t.alloc(10, "differentName", fill=b"different\0"))
        t.w32(node + 12, nodes[i + 1] if i + 1 < count else 0)
        t.w32(node + 16, h if i == hit or (scenario == 5 and i == count - 1) else h ^ (1 << r.randrange(32)))
    table = t.alloc(8, "memberList")
    t.w32(table, nodes[0] if nodes else 0)
    # The tail is irrelevant: also exercise a stale/null tail on nonempty lists.
    t.w32(table + 4, r.choice((0, nodes[-1] if nodes else t.u32())))
    t.args(r3=table, r4=name)
