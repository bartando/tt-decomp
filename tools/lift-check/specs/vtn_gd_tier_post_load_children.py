"""gdTier::PostLoadChildren (0x821F0F10): count children (+0xC, next +8) whose
slot 20 IsType(g_gdTierMember_typeId) holds, logging the others' slot 19 name;
allocate the member array once (+0x14, cap +0x1A), set the count (+0x18) and
fill it. Checks the xmlNodeStruct slot dispatch and gdTier's layout."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "gdTier::PostLoadChildren"
ADDRESS = 0x821F0F10
SOURCE = "src/game/data/gd_data.cpp"
RET = None
EXTERNS = {"rage_DebugLog": 0x8240E6D0, "rage_alloc": 0x820DEC88}   # both names carry other addresses elsewhere

MATCH = {}


def _is_type(ctx):
    ctx.ret(r3=MATCH[ctx.r(3)])


CALLS = {
    "child.vfn_20": model(_is_type),
    "child.vfn_19": stub(args=("r3",)),
    0x8240E6D0: stub(ret="void", args=("r3", "r4")),
    0x820DEC88: alloc(size_reg="r3"),
}


def inputs(t):
    obj = t.alloc(0x20, "gdTier")
    vt = t.vtable("child", 24)
    MATCH.clear()
    nxt = 0
    for i in range(t.rng.randrange(5)):
        c = t.alloc(0x10, f"c{i}")
        t.w32(c, vt)
        t.w32(c + 8, nxt)
        MATCH[c] = t.rng.choice([0, 1, 0x100, 0xFF01])
        nxt = c
    t.w32(obj + 0xC, nxt)
    t.w16(obj + 0x1A, 0 if t.rng.random() < 0.7 else 3)
    t.w32(obj + 0x14, t.alloc(0x20, "oldArr"))
    t.args(r3=obj)
