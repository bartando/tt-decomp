"""Shared inputs for pongCSAction specs: an action with 0..4 children (+0x08 array,
+0x0C u16 count) whose vtables are fake, and action data at +0x04 (enabled byte +0x10)."""


def cs_action(t, max_children=4):
    act = t.alloc(0x20, "action")
    data = t.alloc(0x20, "data")
    t.w8(data + 0x10, t.rng.choice([0, 1, 1]))
    t.w32(act + 4, data)
    n = t.rng.randrange(0, max_children + 1)
    arr = t.alloc(4 * max(n, 1), "children")
    vt = t.vtable("child", slots=16)
    for i in range(n):
        c = t.alloc(0x20, f"child{i}")
        t.w32(c, vt)
        t.w32(arr + 4 * i, c)
    t.w32(act + 8, arr)
    t.w16(act + 0xC, n)
    return act
