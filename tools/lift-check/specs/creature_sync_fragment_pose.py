"""pongCreature::SyncFragmentPose: skeleton pose -> fragment cache entry's skeleton,
per bone record (fragType +0x1AF bit 2) or one memcpy of the matrices."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::SyncFragmentPose"
ADDRESS = 0x820C6B68
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    # slot 2 returns a bool (the asm tests its low byte; clang trusts a bool is 0 or 1)
    "bound.vfn_2": stub(ret=lambda ctx: ctx.rng.choice([0, 1])),
    "bound.vfn_3": stub(ret="void", args=("r3", "r4")),
}


def skeleton(t, name, data, bones):
    s = t.alloc(0x20, name)
    t.w32(s + 0x04, data)
    t.w32(s + 0x0C, t.alloc(0x50 * bones + 0x10, name + ".bones"))
    t.w32(s + 0x14, t.alloc(0x40 * bones + 0x10, name + ".boneMatrices"))
    return s


def inputs(t):
    rng = t.rng
    bones = rng.choice([0, 1, 3, 7])
    creature = t.alloc(0x170, "creature")

    if rng.random() < 0.9:
        char = t.alloc(0x20, "char")
        t.w32(char + 0x18, t.alloc(0x10, "char+18") if rng.random() < 0.9 else 0)
    else:
        char = 0
    t.w32(creature + 0xA0, char)

    data = t.alloc(0x20, "skeletonData")
    t.w16(data + 0x0C, bones)
    src = skeleton(t, "source", data, bones)
    dst = skeleton(t, "target", t.alloc(0x20, "targetData"), bones)
    t.w32(creature + 0xAC, src)

    entry = t.alloc(0x1F0, "cacheEntry")
    t.w32(entry + 0x1E4, dst)

    ftype = t.alloc(0x1B0, "fragType")
    t.w8(ftype + 0x1AF, rng.getrandbits(8))

    inst = t.alloc(0x130, "inst")
    t.w32(inst, t.vtable("inst", 48))
    t.w32(inst + 0x54, entry)
    r = rng.random()
    if r < 0.4:
        holder = t.alloc(0x48, "typeHolder")
        t.w32(holder + 0x18, ftype if rng.random() < 0.8 else 0)
        t.w32(inst + 0x94, holder)
    else:
        t.w32(inst + 0x94, 0)
        t.w32(inst + 0x90, ftype if r < 0.85 else 0)
    bound = t.alloc(0x20, "bound")
    t.w32(bound, t.vtable("bound", 8))
    arch = t.alloc(0x20, "archetype")
    t.w32(arch + 0x0C, bound)
    t.w32(inst + 0x04, arch)
    t.w32(creature + 0xA4, inst)
    t.args(r3=creature)
