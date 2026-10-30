"""Frame command dispatch and play-state transitions.

The event helper and virtual calls are modeled, not executed: real ActionScript
and command side effects are outside this spec. Models mutate frame/state and
next pointers to exercise when the original reads them, and call traces check
order, slots and arguments. Frame indices are bounded to the allocated table.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfFILE::AdvanceDefinitionFrame"
ADDRESS = 0x82403628
SOURCE = "src/rage/swf.cpp"
TRIALS = 400


def event(ctx):
    instance = ctx.r(3)
    # Event dispatch may change the frame and play flag before table lookup.
    ctx.write(instance + 0xA4, ctx.read(instance + 0xC0, 2))
    ctx.write(instance + 0xAA, ctx.read(instance + 0xC2, 1))


def command(ctx):
    instance = ctx.r(4)
    node = ctx.r(3)
    # Commands can change play/stop requests and their own next link.
    ctx.write(instance + 0xAA, ctx.read(node + 0x10, 1))
    ctx.write(instance + 0xAB, ctx.read(node + 0x11, 1))
    ctx.write(instance + 0xAC, ctx.read(node + 0x12, 1))
    ctx.write(node + 0x0C, ctx.read(node + 0x14, 4))


CALLS = {
    0x823FD3E8: model(event, args=("r3", "r4", "r5")),
    "command.vfn_1": model(command, args=("r3", "r4")),
    "command.vfn_3": model(command, args=("r3", "r4")),
    "instance.vfn_2": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    file = t.alloc(0x20, "file")
    instance = t.alloc(0xD0, "instance")
    table = t.alloc(8 * 4, "frames", fill="zero")
    t.w32(file + 0x0C, table)
    t.w32(instance, t.vtable("instance"))
    t.w16(instance + 0xA4, rng.randrange(4))
    t.w16(instance + 0xC0, rng.randrange(4))
    for offset in (0xAA, 0xAB, 0xAC, 0xC2):
        t.w8(instance + offset, rng.choice((0, 0, 1, 2, 255)))
    for frame in range(4):
        head = 0
        for _ in range(rng.randrange(4)):
            node = t.alloc(0x18, "command")
            t.w32(node, t.vtable("command"))
            # The link changes during the call; iteration must read it afterward.
            t.w32(node + 0x0C, 0)
            t.w32(node + 0x14, head)
            for offset in (0x10, 0x11, 0x12):
                t.w8(node + offset, rng.choice((0, 0, 1, 2, 255)))
            head = node
        t.w32(table + frame * 8 + 4, head)
    t.args(r3=file, r4=instance)
