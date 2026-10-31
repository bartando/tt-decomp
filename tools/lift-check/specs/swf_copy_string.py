"""Copy exact twelve-byte chunks from a padded, terminated input into its pool.

The free list always has enough nodes, as required by retail. Bytes after the
terminator are randomized and checked too. Counts include 16-bit underflow.
"""
from liftcheck.spec import *

FUNCTION = "swfCopyString"
ADDRESS = 0x823FABC0
SOURCE = "src/rage/swf_text.cpp"
TRIALS = 500


def inputs(t):
    rng = t.rng
    length = rng.choice((0, 1, 11, 12, 13, 23, 24, 25, 63, 64, 255, rng.randrange(1000)))
    count = length // 12 + 1
    text = t.alloc(count * 12, "source")
    t.put(text, bytes(rng.randrange(1, 256) for _ in range(length)) + b"\0")
    pool = t.alloc(20, "pool")
    nodes = [t.alloc(16, "freeChunk") for _ in range(count + rng.randrange(1, 5))]
    rng.shuffle(nodes)
    for i, node in enumerate(nodes):
        t.w32(node, nodes[i + 1] if i + 1 < len(nodes) else 0)
    t.w32(pool + 12, nodes[0])
    t.w16(pool + 6, rng.choice((0, 1, 0xffff, len(nodes), rng.randrange(65536))))
    t.w32(0x82602844, pool)  # g_swfTextPool
    t.args(r3=text)
