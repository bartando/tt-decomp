"""Full shot copy and lock flags, including enable changes during the copy."""
from liftcheck.spec import *

FUNCTION = "CopyVectorThreadSafe"
ADDRESS = 0x82287040
SOURCE = "src/game/ball/ball_prediction_copy_locked.cpp"
TRIALS = 256

def copy(ctx):
    destination, source = ctx.r(3), ctx.r(4)
    # Same fields as the real assignment, with the original padding preserved.
    fields = [(0, 12), (0x10, 16), (0x20, 4), (0x30, 0x84), (0xB4, 1), (0xB6, 2)]
    for offset, size in fields:
        ctx.write(destination + offset, ctx.read(source + offset, size))
    change = ctx.read(source + 0xB8, 1)[0]
    if change != 2:
        ctx.write(destination - 0x40 + 0x105, bytes([change]))
    return destination

CALLS = {
    "ballPredict_CopyShot": model(copy, args=("r3", "r4"), deref={"r4": 0xB8}),
    "nop_8240E6D0": stub(ret="void", args=("r3",)),
}

def inputs(t):
    context = t.alloc(0x120, "context")
    source = t.alloc(0xC0, "shot")
    t.w8(context + 0x105, [0, 1, 2, 255][t.index % 4])
    t.w8(source + 0xB8, (t.index // 4) % 3)
    t.args(r3=context, r4=source)
