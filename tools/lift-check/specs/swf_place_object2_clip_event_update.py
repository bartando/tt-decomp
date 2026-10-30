"""Slot 3: unsigned sorted depth lookup, replace events, then enter-frame dispatch.

Both helpers are modeled boundaries. Event replacement writes the child's
fields, changes the command and unlinks the child; dispatch must still receive
that same child and the retail enter-frame mask/name. Empty lists, every hit
position, gaps, early-stop and uint16 boundaries are covered. No ignored bytes.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfCMD_PlaceObject2ClipEvent::UpdateClipEvents"
ADDRESS = 0x824084B0
SOURCE = "src/rage/swf.cpp"
TRIALS = 1200


def word(c, address):
    return int.from_bytes(c.read(address, 4), "big")


def replace_events(c):
    child = c.r(3)
    c.write(child + 0xC4, c.r(4).to_bytes(4, "big"))
    c.write(child + 0xC8, c.r(5).to_bytes(4, "big"))
    command, parent = word(c, child + 0xD4), word(c, child + 0xD8)
    c.write(command + 0x20, c.rng.randbytes(12))
    c.write(parent + 0xB4, bytes(4))
    c.ret(r3=child)  # Retail swfSetClipEvents preserves the instance in r3.


def dispatch(c):
    child = c.r(3)
    c.write(child + 0xCC, c.r(4).to_bytes(4, "big"))


CALLS = {
    0x823FD320: model(replace_events, args=("r3", "r4", "r5", "r6")),
    0x823FD3E8: model(dispatch, args=("r3", "r4", "r5")),
}


def inputs(t):
    r = t.rng
    command = t.alloc(0x30, "command")
    parent = t.alloc(0xC0, "parent")
    scenario = t.index % 8
    depths = sorted(r.sample((0, 1, 2, 255, 256, 32767, 32768, 65534, 65535),
                              0 if scenario == 0 else r.randrange(2, 8)))
    if scenario in (1, 2, 3):
        key = depths[(0, len(depths) // 2, len(depths) - 1)[scenario - 1]]
    else:
        key = r.choice((0, 1, 256, 32767, 32768, 65535, r.randrange(65536)))
    head = 0
    for depth in reversed(depths):
        child = t.alloc(0xDC, "child")
        t.w16(child + 0xA6, depth)
        t.w32(child + 0xB8, head)
        t.w32(child + 0xD4, command)
        t.w32(child + 0xD8, parent)
        head = child
    t.w32(parent + 0xB4, head)
    t.w16(command + 0x10, key)
    t.w32(command + 0x20, r.choice((0, 1, 2, 0x80000000, t.u32())))
    t.w32(command + 0x24, r.choice((0, 1, 4, 0xFFFFFFFF, 0x80000000)))
    t.w32(command + 0x28, r.choice((0, t.alloc(48, "eventRecords"))))
    t.args(r3=command, r4=parent)
