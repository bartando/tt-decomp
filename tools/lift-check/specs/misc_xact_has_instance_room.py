"""xactGlobalSettings::HasInstanceRoom: the cue's own instance limit, then the
limit of its sound's category and every parent category. The settings' and the
cue's vtable slots are Python models over per-trial tables."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "xactGlobalSettings::HasInstanceRoom"
ADDRESS = 0x8244DA40
SOURCE = "src/game/network/msg_msg_sink.cpp"

T = {}   # this trial's tables (trials run one after another)

CALLS = {
    "cue.vfn_26": stub(ret=lambda ctx: T["hasLimit"]),
    "cue.vfn_25": stub(ret=lambda ctx: T["limitByte"]),
    "gs.vfn_4": stub(ret=lambda ctx: T["max"][ctx.r(4) & 0xFFFF], args=("r3", "r4")),
    "gs.vfn_6": stub(ret=lambda ctx: T["parent"][ctx.r(4) & 0xFFFF], args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    ncat = 8
    gs = t.alloc(0x84, "globalSettings", fill="zero")
    t.w32(gs, t.vtable("gs", 18))
    counts = t.alloc(4 * ncat, "categoryInstanceCounts")
    for c in range(ncat):
        t.w32(counts + 4 * c, rng.choice([0, 1, 2, 3, 5, -1, 300]))
    t.w32(gs + 0x68, counts)
    # parents form chains that end in 0xFFFF (a parent always has a lower index)
    T["parent"] = [0xFFFF] + [rng.choice([0xFFFF, rng.randrange(c)]) for c in range(1, ncat)]
    T["max"] = [rng.choice([0xFF, 0xFF, 0, 1, 2, 4, 200]) for _ in range(ncat)]

    cue = t.alloc(0x128, "cue", fill="zero")
    t.w32(cue, t.vtable("cue", 27))
    T["hasLimit"] = rng.choice([0, 1, 1, -7])
    limit = t.alloc(4, "limit")
    t.w8(limit, rng.choice([0, 1, 2, 3, 0xFF]))
    T["limitByte"] = limit
    bank = t.alloc(0x100, "soundBank", fill="zero")
    cues = t.alloc(4 * 4, "cueInstanceCounts")
    for k in range(4):
        t.w32(cues + 4 * k, rng.choice([0, 1, 2, 4, -3]))
    t.w32(bank + 0xF8, cues)
    t.w32(cue + 0x11C, bank)
    t.w16(cue + 0x124, rng.randrange(4))
    if rng.random() < 0.85:
        rec = t.alloc(4, "soundRecord")
        t.w8(rec, rng.getrandbits(8))
        t.w16(rec + 1, rng.choice([0xFFFF] + list(range(ncat))))
        snd = t.alloc(0x20, "sound", fill="zero")
        t.w32(snd + 0x1C, rec)
        t.w32(cue + 0x34, snd)
    t.args(r3=gs, r4=cue)
