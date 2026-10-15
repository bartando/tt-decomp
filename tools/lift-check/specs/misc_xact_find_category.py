"""xactGlobalSettings::FindCategory: friendly-name lookup in the .xgs image's hash
table under the engine lock. The image accessors (vtable slots) are Python
models over a small image built per trial; the hash (0x82448290) runs as the
original, and names are placed in the buckets a Python copy of it picks."""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "xactGlobalSettings::FindCategory"
ADDRESS = 0x8244CA80
SOURCE = "src/game/network/msg_msg_sink.cpp"

HDR = {}   # this trial's image layout (trials run one after another)

# header offsets: flags +0x08, counts +0x09/+0x0B, bucket counts +0x0D/+0x0F,
# category buckets/entries +0x1F/+0x23, variable buckets/entries +0x27/+0x2B
BUCKETS_OFF, ENTRIES_OFF = 0x1F, 0x23


def name_hash(s, n):
    h = 0
    for c in s:
        sc = c - 256 if c >= 128 else c
        h = (((h & 0xFFFF) * 3) & 0xFFFF) + ((h >> 1) & 0x7FFF) + (sc & 0xFFFF)
    return (h & 0xFFFF) % n


def _cstr(ctx, p):
    out = b""
    while True:
        c = ctx.read(p + len(out), 1)
        if c == b"\0":
            return out
        out += c


def _strcmp(ctx):
    """The original inlines strcmp; the lift calls it (0x82432970, which
    lift-check doesn't model), so model it here and keep it out of the trace."""
    a, b = _cstr(ctx, ctx.r(3)), _cstr(ctx, ctx.r(4))
    ctx.ret(r3=(a > b) - (a < b))


CALLS = {
    0x82448290: run(),
    0x82432970: model(_strcmp, transparent=True),
    0x82585E0C: stub(ret="void"),     # RtlEnterCriticalSection
    0x82585DFC: stub(ret="void"),     # RtlLeaveCriticalSection
    "gs.vfn_11": stub(ret=lambda ctx: HDR["image"]),
    "gs.vfn_12": stub(ret=lambda ctx: HDR["buckets"]),
    "gs.vfn_13": stub(ret=lambda ctx: HDR["entries"] + 6 * (ctx.r(4) & 0xFFFF), args=("r3", "r4")),
    "gs.vfn_14": stub(ret=lambda ctx: HDR["image"] + ctx.r(4), args=("r3", "r4")),
    "gs.vfn_9": stub(ret=lambda ctx: 0x1000 + (ctx.r(4) - HDR["entries"]) // 6, args=("r3", "r4")),
}

WORDS = [b"Music", b"Default", b"Global", b"FX", b"Voice", b"Crowd", b"Ball", b"Menu",
         b"AttackTime", b"ReleaseTime", b"NumCueInstances", b"SpeedOfSound", b"\xe9t\xe9"]


def inputs(t):
    rng = t.rng
    gs = t.alloc(0x84, "globalSettings", fill="zero")
    t.w32(gs, t.vtable("gs", 18))
    engine = t.alloc(0xB0, "engine")
    t.w32(gs + 4, engine)

    n = rng.choice([0, 1, 3, 8])
    nb = rng.choice([1, 2, 5, 16])
    names = rng.sample(WORDS, n)
    img = t.alloc(0x400, "image", fill="zero")
    HDR["image"] = img
    flags = rng.choice([0, 1, 2, 3, 3, 3])
    t.w8(img + 0x08, flags)
    t.w16(img + 0x09, n)
    t.w16(img + 0x0B, n if rng.random() < 0.85 else 0)
    t.w16(img + 0x0D, nb)
    t.w16(img + 0x0F, nb)
    buckets, entries, strings = 0x40, 0x80, 0x100
    t.w32(img + BUCKETS_OFF, buckets)
    t.w32(img + ENTRIES_OFF, entries)
    HDR["buckets"] = img + buckets
    HDR["entries"] = img + entries
    heads = [0xFFFF] * nb
    off = strings
    for i, nm in enumerate(names):
        t.put(img + off, nm + b"\0")
        b = name_hash(nm, nb) if rng.random() < 0.9 else rng.randrange(nb)
        t.w32(img + entries + 6 * i, off)
        t.w16(img + entries + 6 * i + 4, heads[b])
        heads[b] = i
        off += len(nm) + 1
    for b in range(nb):
        t.w16(img + buckets + 2 * b, heads[b])

    probe = t.alloc(32, "name")
    pick = rng.choice(names + [b"Nope", b"Musi", b"Music2"]) if names else b"Music"
    t.put(probe, pick + b"\0")
    t.args(r3=gs, r4=probe)
