"""xactGlobalSettingsImage::Initialize: stores the image, counts RPCs whose
parameter is above 2, then calls CreateRuntimeState (0x8244CD40, stubbed).
GetHeader (slot 11) is modelled as returning the image (+0x84)."""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "xactGlobalSettingsImage::Initialize"
ADDRESS = 0x8244B870
SOURCE = "src/game/network/msg_msg_sink.cpp"
EXTERNS = {"xactGlobalSettings::CreateRuntimeState": 0x8244CD40}


def header(ctx):
    return struct.unpack(">I", ctx.read(ctx.r(3) + 0x84, 4))[0]


CALLS = {
    "gs.vfn_11": stub(ret=header),
}


def inputs(t):
    rng = t.rng
    gs = t.alloc(0x94, "image", fill="zero")
    t.w32(gs, t.vtable("gs", 18))
    data = t.alloc(0x400, "xgs", fill="zero")
    n = rng.choice([0, 1, 2, 4, 7])
    t.w16(data + 0x11, n)
    off = 0x40
    t.w32(data + 0x37, off)
    for _ in range(n):
        pts = rng.randrange(4)
        t.w16(data + off, rng.getrandbits(16))
        t.w8(data + off + 2, pts)
        t.w16(data + off + 3, rng.choice([0, 1, 2, 3, 4, 9, 0x8000]))
        off += 5 + 9 * pts
    t.w16(gs + 0x64, rng.getrandbits(16))
    t.args(r3=gs, r4=data, r5=rng.randrange(0x10000), r6=rng.choice([0, 1]), r7=t.u32())
