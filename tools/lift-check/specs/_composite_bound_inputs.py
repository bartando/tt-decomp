"""Small, acyclic composite trees with empty, null and non-composite children."""
def tree(t, depth=0):
    rng = t.rng
    bound = t.alloc(0xA0, f"compositeDepth{depth}AndGuards")
    t.w8(bound + 4, 9)
    count = rng.choice((0, 1, 2, 4, 6))
    children = t.alloc(max(4, count * 4), f"childrenDepth{depth}")
    t.w32(bound + 0x70, children)
    t.w16(bound + 0x82, count)
    total = count
    for i in range(count):
        kind = rng.randrange(4)
        child = 0
        if kind == 0 and depth < 3:
            child, descendants = tree(t, depth + 1)
            total += descendants
        elif kind in (1, 2):
            child = t.alloc(32, f"leafDepth{depth}")
            t.w8(child + 4, rng.choice((0, 1, 5, 8, 10, 255)))
        t.w32(children + i * 4, child)
    return bound, total


def index_inputs(t):
    bound, total = tree(t)
    # Negative/direct/first descendant/last valid/out-of-range/large indices.
    index = t.rng.choice((-2, -1, 0, 1, 2, 5, total - 1, total,
                          total + 1, 32768, 0x7FFFFFFF))
    t.args(r3=bound, r4=index)
