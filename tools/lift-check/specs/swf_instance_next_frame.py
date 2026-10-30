"""Next-frame wrapping and play-state save/restore around retail vtable slot 1.

The callback checks playing==1, changes it, and mutates the current frame. Full
context words and poisoned upper bits catch forwarding/truncation mistakes.
NextFrame is void: slot-2 caller 0x823FE720 returns without reading r3;
the VM slot-2 call at 0x823FFDCC also discards it.
"""
from liftcheck.spec import *

FUNCTION = "rage::swfINSTANCE::NextFrame"
ADDRESS = 0x823FB8A0
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000
RET = None


def _goto(ctx):
    instance = ctx.r(3)
    assert ctx.read(instance + 0xAA, 1) == b"\1"
    ctx.write(instance + 0xAA, bytes((ctx.rng.choice((0, 2, 255)),)))
    ctx.write(instance + 0xA4, ctx.rng.randbytes(2))
    ctx.ret(r3=ctx.rng.getrandbits(32))


CALLS = {"instance.vfn_1": model(_goto, args=("r3", "r4", "r5"))}


def inputs(t):
    rng = t.rng
    instance = t.alloc(0xD0, "instance")
    definition = t.alloc(16, "definition")
    count = rng.choice((0, 1, 2, 8, 0xFFFF))
    t.w32(instance, t.vtable("instance"))
    t.w32(instance + 4, definition)
    t.w16(definition + 8, count)
    t.w16(instance + 0xA4, rng.choice((0, 1, max(0, count - 1), count, 0xFFFE, 0xFFFF)))
    t.w8(instance + 0xAA, rng.choice((0, 1, 2, 128, 255)))
    t.args(r3=instance, r4=rng.choice((0, 1, 255, 0x100, 0x12345678, 0xFFFFFFFF, rng.getrandbits(32))))
