"""pongCreatureInst::AttachToScene (slot 41): key-count check, attach flag,
manager callback (+0x32C), slot 48 with a type, insert into the holder's list."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst::AttachToScene"
ADDRESS = 0x8211D0E0
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    # CacheKeyMap::Find (own spec). The probe on the stack leaves its last two
    # bytes unset on both sides, so compare only key and count.
    0x82121660: stub(ret=lambda ctx: ctx.rng.choice([0, 0x40000F00]), args=("r3",), deref={"r4": 6}),
    "onAttach": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    mgr = t.alloc(0x380, "manager")
    pool = t.alloc(0x20, "pool")
    t.w32(pool + 0x1C, t.alloc(0x10, "keyMap"))
    t.w32(mgr + 0x2F0, pool)
    t.w32(mgr + 0x32C + 0x0C, t.fake_fn("onAttach"))
    t.w32(0x826063B8, mgr)

    inst = t.alloc(0x130, "inst")
    t.w32(inst, t.vtable("inst", 60))
    t.w32(inst + 0x98, rng.choice([0, rng.getrandbits(32)]))
    t.w32(inst + 0x90, rng.choice([0, t.alloc(0x10, "type")]))
    if rng.random() < 0.7:
        holder = t.alloc(0x48, "holder")
        t.w32(holder + 0x18, rng.choice([0, t.alloc(0x10, "holderType")]))
        if rng.random() < 0.7:
            head = t.alloc(0x60, "head")
            prev = t.alloc(0x60, "prev") if rng.random() < 0.5 else 0
            t.w32(head + 0x58, prev)
            t.w32(holder + 0x3C, head)
        else:
            t.w32(holder + 0x3C, 0)
        t.w32(holder + 0x44, rng.randrange(10))
    else:
        holder = 0
    t.w32(inst + 0x94, holder)
    t.args(r3=inst, r4=rng.choice([0, 1]))
