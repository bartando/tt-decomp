from liftcheck.spec import *


def release(ctx):
    state = ctx.r(3) - 0x20
    # Disposal may update fields the lifecycle functions subsequently reload.
    if ctx.rng.randrange(2):
        ctx.write(state + 0x48, b"\0\2")
        ctx.write(state + 0x4A, b"\x40\0")


CALLBACKS = {
    "release": model(release, args=("r3",)),
    0x8225FFF8: stub(ret="void", args=("r3", "r4")),
}


def state(t):
    obj = t.alloc(0xA0, "blender", floats=[0x50, 0x54, 0x78, 0x7C, 0x80, 0x84, 0x88, 0x98, 0x9C])
    # PPC copies two uninitialized stack words into unused callback slots.
    # They are never read by these lifecycle routines or callback disposal.
    t.ignore(obj + 0x24, 4)
    t.ignore(obj + 0x34, 4)
    t.w16(obj + 0x48, t.rng.choice([0, 1, 2, 0x100, 0xFFFF]))
    t.w16(obj + 0x4A, t.rng.choice([0, 1, 0x20, 0x100, 0x800, 0x801, 0xFFFF]))
    t.w32(obj + 0x2C, t.fake_fn("release"))
    for i in range(4):
        t.w32(0x8261A0C0 + 4 * i, t.rng.getrandbits(32))
    return obj
