from liftcheck.spec import *

HEAD = 0x826066E0
_owned = {}
_head_after_clear = 0
_name_after_clear = 0


def heap(t):
    sda = t.alloc(16, "sda")
    thread = t.alloc(16, "thread")
    allocator = t.alloc(16, "heap")
    t.w32(sda, thread)
    t.w32(thread + 4, allocator)
    t.w32(allocator, t.vtable("heap", 3))
    t.w32(0x82600000, sda)
    return sda, thread, allocator


def linked(t, target):
    nodes = [t.alloc(0x17C, "otherFont") for _ in range(3)]
    t.w32(nodes[0] + 0x174, nodes[1])
    t.w32(nodes[1] + 0x174, nodes[2])
    t.w32(nodes[2] + 0x174, 0)
    t.w32(target + 0x174, nodes[1])
    mode = t.index % 4
    if mode == 0:
        return target
    if mode == 1:
        t.w32(nodes[0] + 0x174, target)
    return nodes[0] if mode != 3 else 0


def clear_boundary(c):
    c.write(HEAD, _head_after_clear.to_bytes(4, "big"))
    c.write(c.r(3) + 0x170, _name_after_clear.to_bytes(4, "big"))


DESTROY_CALLS = {
    0x82409F08: model(clear_boundary, args=("r3",)),
    0x820C00C0: stub(ret="void", args=("r3",)),
}


def destroy_inputs(t):
    global _head_after_clear, _name_after_clear
    font = t.alloc(0x17C, "font")
    _head_after_clear = linked(t, font)
    t.w32(HEAD, t.alloc(0x17C, "previousHead"))
    _name_after_clear = t.alloc(16, "newName", fill=b"arial12\0") if t.rng.randrange(2) else 0
    t.w32(font + 0x170, t.alloc(16, "oldName", fill=b"old\0"))
    for offset in (0, 8, 16, 24, 32):
        t.w32(font + offset, t.alloc(16, "ownedArray") if t.rng.randrange(2) else 0)
        t.w16(font + offset + 6, t.rng.choice((0, 1, 2, 65535)))
    t.args(r3=font)


RELEASE_CALLS = {
    0x82409490: stub(ret="void", args=("r3",)),
    0x820C00C0: stub(ret="void", args=("r3",)),
    0x8240E6D0: stub(ret="void", args=("r3",)),
}


def release_inputs(t):
    font = t.alloc(0x17C, "font")
    t.w32(HEAD, linked(t, font))
    t.w32(font + 0x178, t.rng.choice((0, 1, 1, 2, 0xffffffff)))
    t.args(r3=font if t.index % 7 else 0)


def ownership(c):
    c.ret(r3=_owned[c.r(3)])


CLEAR_CALLS = {
    0x820C2E18: stub(ret=0, args=("r3",)),
    0x821512B8: stub(ret=0, args=("r3", "r4")),
    0x820F90D0: model(ownership, args=("r3",)),
    "heap.vfn_2": stub(ret="void", args=("r3", "r4")),
}


def clear_inputs(t):
    global _owned
    rng = t.rng
    _owned = {}
    font = t.alloc(0x17C, "font")
    sda, thread, allocator = heap(t)
    textures = rng.randrange(5)
    effects = rng.randrange(5)
    for offset, count in ((0, textures), (16, textures), (8, effects), (24, effects)):
        data = t.alloc(max(1, count) * 4, "pointerArray")
        t.w32(font + offset, data)
        t.w16(font + offset + 4, count if offset < 16 else rng.randrange(10))
        for i in range(count):
            item = t.alloc(0x24, "resource") if rng.randrange(3) else 0
            t.w32(data + i * 4, item)
            if item:
                t.w32(item + 0x20, rng.choice((0, 1, 2, 0xffffffff)))
        _owned[data] = rng.choice((0, 0x100, 1, 0x101))
    for offset in (0x20, 0x170, 0x64):
        data = t.alloc(16, "sideBlock") if rng.randrange(2) else 0
        t.w32(font + offset, data)
        if data:
            _owned[data] = rng.choice((0, 0x100, 1, 0x101))
    t.args(r3=font, r13=sda)
    return font, sda, thread, allocator
