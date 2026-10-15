"""pongCreature::Reset (vtable 0x82027B08 slot 3); `this` is the
phUpdateObject base (creature + 0x10), offsets below are from it."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::Reset"
ADDRESS = 0x820C6840
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    "host.vfn_5": stub(ret="void", args=("r3", "r4")),
    # phUpdateObject's Reset(this, world, scene) and pongMover::Reset(mover, flip)
    0x8227D5B0: stub(ret="void", args=("r3", "r4", "r5")),
    0x820C9F40: stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    base = t.alloc(0x100, "updateBase")
    t.w8(base + 0xE0, rng.choice([0, 1]))
    host = t.alloc(0x10, "host")
    t.w32(host, t.vtable("host", 8))
    t.w32(base + 0xE4, host)
    block = t.alloc(0x50, "colliderBlock")
    sub = t.alloc(0x10, "colliderSub")
    t.w32(sub, t.vtable("colliderSub", 8))
    t.w32(block + 0x34, sub)
    t.w32(block + 0x30, t.alloc(0x30, "activeAnim", floats=[0x20]) if rng.random() < 0.7 else 0)
    t.w32(base + 0xE8, block)

    t.w32(base + 0x94, t.alloc(0x40, "charData"))
    t.w32(base + 0x9C, t.alloc(0x40, "charCtx"))
    t.w32(base + 0xAC, t.alloc(0x40, "animBlock"))
    t.w32(base + 0x98, t.alloc(0x40, "mover"))
    idx = rng.choice([0, 1])
    t.w32(base + 0xBC, idx)

    render = t.alloc(0x130, "renderObj")
    t.w32(render + 0x128, rng.choice([0, 1, -1]))
    t.w32(0x825EAB2C, render)
    t.w32(0x825EAB28, t.alloc(0x60, "inputTable"))
    t.args(r3=base, r4=rng.getrandbits(32), r5=rng.getrandbits(32))
