"""pongDrawBucket_AddEntry (0x822278D8): renderable slot 1, then for each layer whose mask
bit is set (stopping once the mask is empty) bumps the layer's count for the current
buffer (0x826065DC) and appends the renderable. The old lift indexed by layer, not buffer,
and read the header at the wrong offsets."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongDrawBucket_AddEntry"
ADDRESS = 0x822278D8
SOURCE = "src/game/pong_render.cpp"
EXTERNS = {"rage_debugLog": 0x8240E6D0, "g_phFrameIndex": 0x826065DC}

CALLS = {
    "rend.vfn_1": stub(ret="void"),
    # r3 is the 71-byte format string at 0x8204DF20; strings that long compare as pointers
    0x8240E6D0: stub(ret="void", args=("r4", "r5")),
}


def inputs(t):
    buf = t.rng.randrange(2)
    t.w32(0x826065DC, buf)
    nlayers = t.rng.randrange(0, 5)
    bucket = t.alloc(0x60, "bucket")
    t.w8(bucket + 0x50, t.rng.choice([0, 1, 1, 1]))
    t.w16(bucket + 0x0C, nlayers)
    data = t.alloc(4 * max(nlayers, 1), "layers")
    t.w32(bucket + 0x08, data)
    for i in range(nlayers):
        desc = t.alloc(0x40, f"desc{i}")
        t.w32(data + 4 * i, desc)
        cap = t.rng.randrange(1, 6)
        t.w32(desc + (buf + 13) * 4, t.rng.randrange(0, cap + 1))
        t.w16(desc + (buf + 5) * 8, cap)
        t.w32(desc + buf * 8 + 0x24, t.alloc(4 * (cap + 1), f"entries{i}"))
    rend = t.alloc(0x10, "rend")
    t.w32(rend, t.vtable("rend", slots=4))
    t.args(r3=bucket, r4=rend, r5=t.rng.choice([0, 1, 2, 5, 0xF, t.u32()]))
