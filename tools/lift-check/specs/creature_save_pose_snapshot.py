"""pongCreature::SavePoseSnapshot (was RestorePoseFromRollback; vtable 0x82027B08 slot 1).

`this` is the phUpdateObject base (creature + 0x10). The 50-word snapshot
table sits at this + (0x826065DC's index + 50) * 4.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreature::SavePoseSnapshot"
ADDRESS = 0x820C67C0
SOURCE = "src/game/creature/pong_creature.cpp"

# ph_update_object.cpp marks another g_phFrameIndex at 0x825C4898; the asm
# here reads 0x826065DC (lis -0x7DA0; lwz 0x65DC).
EXTERNS = {"g_phFrameIndex": 0x826065DC}


def inputs(t):
    rng = t.rng
    bones = rng.choice([0, 1, 4])
    idx = rng.randrange(50)
    base = t.alloc(0x200, "updateBase")
    snap = t.alloc(0x40 * bones + 0x10, "snapshot") if rng.random() < 0.85 else 0
    t.w32(base + (idx + 50) * 4, snap)
    t.w32(0x826065DC, idx)

    # +0x90 -> +0x14 -> +0x40 -> * -> * -> byte +0x11 (the asm's chain)
    desc = t.alloc(0x20, "desc")
    t.w8(desc + 0x11, rng.getrandbits(8))
    ref = t.alloc(0x20, "descRef")
    t.w32(ref, desc)
    t.w8(ref + 0x11, rng.getrandbits(8))    # one deref short: must not decide
    anim = t.alloc(0x10, "anim")
    t.w32(anim, ref)
    sub = t.alloc(0x50, "sub")
    t.w32(sub + 0x40, anim)
    ch = t.alloc(0x20, "char")
    t.w32(ch + 0x14, sub)
    t.w32(base + 0x90, ch)

    meta = t.alloc(0x10, "meta")
    t.w16(meta + 0x0C, bones)
    ctx = t.alloc(0x20, "charCtx")
    t.w32(ctx + 0x04, meta)
    t.w32(ctx + 0x14, t.alloc(0x40 * bones + 0x10, "pose"))
    t.w32(base + 0x9C, ctx)
    t.args(r3=base)
