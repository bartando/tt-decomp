"""xactGlobalSettings::Dtor: releases the DSP effect through the engine's effect
factory (slot 4), frees the four per-category arrays and deletes the variables.

As in misc_xact_image_dtor, an empty variables array is left out: the original
frees it through the thunk 0x820C0120, the lift calls rage_free directly."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "xactGlobalSettings::Dtor"
ADDRESS = 0x8244C980
SOURCE = "src/game/network/msg_msg_sink.cpp"
EXTERNS = {"XMemFree": 0x820C02D0}

CALLS = {
    "factory.vfn_4": stub(ret="void", args=("r3", "r4")),
    "vars.vfn_0": stub(args=("r3", "r4")),
    0x820C02D0: stub(ret="void", args=("r3", "r4")),
}


def maybe(t, name, size):
    return t.alloc(size, name) if t.rng.random() < 0.75 else 0


def inputs(t):
    rng = t.rng
    gs = t.alloc(0x84, "globalSettings")
    engine = t.alloc(0x20, "engine")
    factory = t.alloc(8, "factory")
    t.w32(factory, t.vtable("factory", 5))
    t.w32(engine + 0x0C, factory)
    t.w32(gs + 4, engine)
    t.w32(gs + 8, maybe(t, "dspEffect", 0x10))
    for off, name in ((0x68, "counts"), (0x6C, "state6C"), (0x70, "state70"), (0x78, "volumes")):
        t.w32(gs + off, maybe(t, name, 0x20))
    if rng.random() < 0.8:
        n = rng.choice([1, 2, 5])
        block = t.alloc(4 + 0xFC * n, "variables")
        t.w32(block, n)
        t.w32(block + 4, t.vtable("vars", 2))
        t.w32(gs + 0x7C, block + 4)
    else:
        t.w32(gs + 0x7C, 0)
    t.args(r3=gs)
