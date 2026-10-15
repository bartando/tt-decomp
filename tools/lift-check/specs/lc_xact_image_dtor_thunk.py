"""misc_xact_image_dtor with empty arrays too: the original frees those through the
thunk 0x820C0120 (`b 0x820C00C0`), the lift calls 0x820C00C0; both are one call.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "xactGlobalSettingsImage::Dtor"
ADDRESS = 0x8244B7E0
SOURCE = "src/game/network/msg_msg_sink.cpp"
EXTERNS = {"XMemFree": 0x820C02D0, "xactGlobalSettings::Dtor": 0x8244C980}

CALLS = {
    "rpc.vfn_0": stub(args=("r3", "r4")),
    0x820C02D0: stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    gs = t.alloc(0x94, "image")
    if rng.random() < 0.8:
        n = rng.choice([0, 1, 2, 3])
        block = t.alloc(4 + 0x30 * max(n, 1), "rpcs")
        t.w32(block, n)
        first = block + 4
        t.w32(first + 4, t.vtable("rpc", 2))
        t.w32(gs + 0x80, first)
    else:
        t.w32(gs + 0x80, 0)
    t.w32(gs + 0x90, rng.choice([0, 1, 0x100]))
    t.args(r3=gs)
