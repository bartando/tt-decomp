from liftcheck.spec import *
CALLS = {0x820DC4E8: run(transparent=True)}

def inputs(t):
    cursor = t.alloc(8, "cursor and capacity")
    low = t.alloc(4, "head")
    high = t.alloc(4, "end")
    values = [-2147483648, -8, -1, 0, 1, 2, 5, 7, 8, 2147483647]
    a, b = [t.rng.choice(values) for _ in range(2)]
    # Exclude the inclusive full signed range, whose remainder traps.
    if a == -2147483648 and b == 2147483647: b -= 1
    t.w32(cursor, t.rng.choice(values))
    t.w32(cursor + 4, t.rng.choice([1, 2, 8, 16]))
    t.w32(low, a)
    t.w32(high, b)
    t.args(r3=cursor, r4=low, r5=high)
