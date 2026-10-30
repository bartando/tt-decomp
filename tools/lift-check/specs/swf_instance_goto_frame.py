"""Timeline stepping, wrap resets and mutable command chains.

Callbacks are modeled with writes and arbitrary r3 values. They may stop the loop
by setting the requested frame, and commands replace their next link on execution.
Frames/tables and finite child/command chains are allocated with bounded frame
counts. GotoFrame is void: slot-1 calls at 0x823FFCFC and 0x823FE588 do not
consume r3 (the latter replaces it at 0x823FE590).
"""
from liftcheck.spec import *

FUNCTION = "rage::swfINSTANCE::GotoFrame"
ADDRESS = 0x823FB7A8
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
RET = None


def _command(ctx):
    node, instance = ctx.r(3), ctx.r(4)
    ctx.write(instance + 0xAA, ctx.read(node + 0x10, 1))
    if ctx.read(node + 0x11, 1) != b"\0":
        ctx.write(instance + 0xA4, ctx.read(instance + 0xC0, 2))
    ctx.write(node + 0x0C, ctx.read(node + 0x14, 4))
    ctx.ret(r3=ctx.rng.getrandbits(32))


def _definition(ctx):
    node, instance = ctx.r(3), ctx.r(4)
    ctx.write(instance + 0xAA, ctx.read(node + 0x10, 1))
    if ctx.read(node + 0x11, 1) != b"\0":
        ctx.write(instance + 0xA4, ctx.read(instance + 0xC0, 2))
    ctx.ret(r3=ctx.rng.getrandbits(32))


CALLS = {"definition.vfn_2": model(_definition, args=("r3", "r4")),
         "command.vfn_2": model(_command, args=("r3", "r4"))}


def inputs(t):
    rng = t.rng
    instance = t.alloc(0xD0, "instance")
    definition = t.alloc(0x20, "definition")
    t.w32(definition, t.vtable("definition"))
    t.w32(instance + 4, definition)
    count = rng.choice((0, 1, 2, 3, 8))
    target = rng.choice((0, max(0, count - 1), rng.randrange(max(1, count)), count, 0xFFFF))
    t.w16(definition + 8, count)
    t.w16(instance + 0xA4, rng.choice((0, max(0, count - 1), rng.randrange(max(1, count)), 0xFFFE, 0xFFFF)))
    t.w16(instance + 0xC0, target)
    t.w8(definition + 0x10, rng.randrange(256))
    t.w8(definition + 0x11, rng.randrange(2))
    table = t.alloc(max(1, count) * 8, "frames")
    t.w32(definition + 0x0C, table)
    for frame in range(count):
        head = 0
        for _ in range(rng.randrange(4)):
            node = t.alloc(0x18, "command")
            t.w32(node, t.vtable("command"))
            t.w32(node + 0x0C, 0)
            t.w32(node + 0x14, head)
            t.w8(node + 0x10, rng.randrange(256))
            t.w8(node + 0x11, rng.randrange(2))
            head = node
        t.w32(table + frame * 8 + 4, head)
    child = 0
    for _ in range(rng.randrange(5)):
        node = t.alloc(0xD0, "child")
        t.w32(node + 0xB8, child)
        t.w8(node + 0xAF, rng.choice((1, 127, 255)))
        child = node
    t.w32(instance + 0xB4, child)
    t.args(r3=instance, r4=(rng.getrandbits(16) << 16) | target,
           r5=rng.choice((0, 1, 255, 0x100, 0x101, rng.getrandbits(32))))
