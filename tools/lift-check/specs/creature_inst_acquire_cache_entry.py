"""pongCreatureInst::AcquireCacheEntry (slot 43): pool entry or slot 57 + null;
binds the entry through 0x8212A700 with slot 53's result."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::AcquireCacheEntry"
ADDRESS = 0x8211EFC0
SOURCE = "src/game/creature/pong_creature.cpp"

# Their `// @` markers sit on the comment line above a declaration, which the
# marker scan doesn't pick up.
EXTERNS = {
    "fragCachePool_Acquire(fragCachePool*)": 0x821263B8,
    "fragCacheEntry_Init": 0x8212A700,
}

ENTRY = {}

CALLS = {
    0x821263B8: model(lambda ctx: ctx.ret(r3=ENTRY["v"])),
    # (entry, holder, type, matrix, inst, index, allocator, markIndex): every
    # register the asm loads.
    0x8212A700: stub(ret="void", args=("r3", "r4", "r5", "r6", "r7", "r8", "r9", "r10")),
}


def inputs(t):
    rng = t.rng
    mgr = t.alloc(0x380, "manager")
    pool = t.alloc(0x20, "pool")
    t.w32(mgr + 0x2F0, pool)
    t.w32(0x826063B8, mgr)
    ENTRY["v"] = t.alloc(0x210, "entry") if rng.random() < 0.8 else 0

    inst = t.alloc(0x130, "inst")
    t.w32(inst, t.vtable("inst", 60))
    t.w32(inst + 0x90, rng.getrandbits(32))
    t.w32(inst + 0x94, rng.getrandbits(32))
    t.args(r3=inst)
