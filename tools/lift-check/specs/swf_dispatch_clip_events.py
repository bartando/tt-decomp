"""Event mask filtering, action headers, VM arguments and script-modified links.

The VM is a model, not executed. It rewires the current node forward and clears
instance.head, so prefetching next or reloading head changes observable calls.
Lists are finite/disjoint; every action buffer has a two-byte header. All six
VM arguments, action bytes and context bytes are compared. No ignored memory.
"""
from liftcheck.spec import *

FUNCTION = "swfDispatchClipEvents"
ADDRESS = 0x823FD3E8
SOURCE = "src/rage/swf.cpp"
TRIALS = 1200


def word(c, address):
    return int.from_bytes(c.read(address, 4), "big")


def execute(c):
    assert c.r(3) == c.r(5) + 2, "VM code must skip its context header"
    assert c.r(6) == c.r(7) == c.r(8) == 0, "VM must start with reset stack/default registers"
    actions, instance = c.r(5), c.r(4)
    node = word(c, actions + 20)
    c.write(node + 4, c.read(actions + 24, 4))
    c.write(instance + 0xC8, bytes(4))
    c.write(instance + 0xCC, c.read(c.r(3), 8))
    c.write(instance + 0xD4, (word(c, instance + 0xD4) + 1).to_bytes(4, "big"))


CALLS = {
    0x823FF7E8: model(execute, args=("r3", "r4", "r5", "r6", "r7", "r8"),
                      deref={"r3": 16, "r5": 18}),
}


def inputs(t):
    r = t.rng
    instance = t.alloc(0xD8, "instance")
    mask = (0, 1, 2, 0x80000000, 0xFFFFFFFF, t.u32())[t.index % 6]
    count = (0, 1, 2, 5, 8)[(t.index // 6) % 5]
    nodes = [t.alloc(8, "eventLink") for _ in range(count)]
    for i, node in enumerate(nodes):
        record = t.alloc(12, "eventRecord")
        actions = t.alloc(32, "headerAndActions")
        flags = r.choice((0, mask, mask ^ 0xFFFFFFFF, 1 << r.randrange(32), t.u32()))
        t.w32(record, flags)
        t.w32(record + 4, actions)
        t.w32(node, record)
        t.w32(node + 4, nodes[i + 1] if i + 1 < count else 0)
        # Re-entry may keep, skip, or remove the remainder of the chain.
        t.w32(actions + 20, node)
        t.w32(actions + 24, r.choice(nodes[i + 1:] + [0]))
    t.w32(instance + 0xC8, nodes[0] if nodes else 0)
    t.w32(instance + 0xD4, 0)
    name = t.alloc(12, "unusedEventName", fill=b"event name\0")
    t.args(r3=instance, r4=mask, r5=name)
