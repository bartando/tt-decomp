"""PlaceObject2 clip execution: base call, sorted child lookup, name and load event.

The base execution, member assignment, event-list setup and dispatch are modeled
boundaries. Lists are finite, sorted and have unique depths; pointers are valid.
The base and member callbacks mutate command fields to exercise read timing.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfCMD_PlaceObject2ClipEvent::Execute"
ADDRESS = 0x824083D8
SOURCE = "src/rage/swf.cpp"
TRIALS = 1200
RET = None


def word(c, addr):
    return int.from_bytes(c.read(addr, 4), "big")


def base(c):
    command, parent = c.r(3), c.r(4)
    replacement = word(c, parent + 0xD4)
    for offset, size in ((0x10, 2), (0x14, 2), (0x20, 16)):
        c.write(command + offset, c.read(replacement + offset, size))
    c.write(parent + 0xB4, c.read(parent + 0xD8, 4))


def member(c):
    parent = c.r(3)
    command = word(c, parent + 0xDC)
    # The caller reloads the name and event fields after the virtual call.
    c.write(command + 0x20, c.read(word(c, parent + 0xE0) + 0x20, 16))


def events(c):
    c.ret(r3=c.r(3))  # The original helper leaves r3 as the instance.


CALLS = {
    0x824081B0: model(base, args=("r3", "r4")),
    "parent.vfn_11": model(member, args=("r3", "r4", "r5"), deref={"r4": 8, "r5": 8}),
    0x823FD320: model(events, args=("r3", "r4", "r5", "r6")),
    0x823FD3E8: stub(ret="void", args=("r3", "r4", "r5")),
}


def inputs(t):
    r = t.rng
    command = t.alloc(0x30, "command")
    after_base = t.alloc(0x30, "afterBase")
    after_member = t.alloc(0x30, "afterMember")
    parent = t.alloc(0xE4, "parent")
    t.w32(parent, t.vtable("parent"))
    t.w32(parent + 0xD4, after_base)
    t.w32(parent + 0xDC, command)
    t.w32(parent + 0xE0, after_member)
    depths = sorted(r.sample((0, 1, 2, 255, 256, 32767, 32768, 65534, 65535), r.randrange(7)))
    key = r.choice(depths) if depths and r.randrange(3) else r.choice((0, 1, 2, 256, 32768, 65535, r.randrange(65536)))
    head = 0
    for depth in reversed(depths):
        node = t.alloc(0xD0, "child")
        t.w16(node + 0xA6, depth)
        t.w32(node + 0xB8, head)
        head = node
    t.w32(parent + 0xB4, 0)
    t.w32(parent + 0xD8, head)
    t.w16(after_base + 0x10, key)
    t.w16(after_base + 0x14, r.choice((0xFFFF, 0, 1, 65534)))
    for obj in (after_base, after_member):
        t.w32(obj + 0x20, t.u32())
        t.w32(obj + 0x24, r.choice((0, 1, 4, 0xFFFFFFFF)))
        t.w32(obj + 0x28, r.choice((0, t.alloc(48, "records"))))
        t.w32(obj + 0x2C, r.choice((0, t.alloc(24, "name", fill=b"child name\0"))))
    t.args(r3=command, r4=parent)
