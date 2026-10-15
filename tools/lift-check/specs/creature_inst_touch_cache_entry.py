"""pongCreatureInst::TouchCacheEntry (0x8211DDB8, slot 22): stamps the cache
entry with the pool's current stamp; returns true."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::TouchCacheEntry"
ADDRESS = 0x8211DDB8
SOURCE = "src/game/creature/pong_creature.cpp"


def inputs(t):
    rng = t.rng
    mgr = t.alloc(0x380, "manager")
    pool = t.alloc(0x20, "pool")
    t.w32(mgr + 0x2F0, pool)
    t.w32(0x826063B8, mgr)
    inst = t.alloc(0x130, "inst")
    t.w32(inst + 0x54, t.alloc(0x20, "entry") if rng.random() < 0.8 else 0)
    t.args(r3=inst)
