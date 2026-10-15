"""LocomotionStateAnim::CopyAnimationData (0x8214C8F8; locomotion.cpp lifts the
same address as LocomotionStateAnim_C8F8_g). Root bone: 0x820DEDC0 with the
helper at +8, or a 64-byte copy; then every further bone i through 0x820DEDC0
(dst + 0x40 * i, src + 0x50 * i, dst + 0x40 * parent[i])."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "LocomotionStateAnim::CopyAnimationData"
ADDRESS = 0x8214C8F8
SOURCE = "src/game/creature/pong_creature.cpp"

CALLS = {
    0x820DEDC0: stub(ret="void", args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    n = rng.choice([0, 1, 2, 5])
    parents = t.alloc(4 * max(n, 1), "parents")
    for k in range(n):
        t.w32(parents + 4 * k, rng.randrange(max(n, 1)))
    info = t.alloc(0x10, "skeletonData")
    t.w32(info + 4, parents)
    t.w16(info + 0x0C, n)
    src = t.alloc(0x50 * max(n, 1), "src")
    t.floats(src, 16, -5.0, 5.0)
    dst = t.alloc(0x40 * max(n, 1), "dst")
    this = t.alloc(0x20, "skeleton")
    t.w32(this + 0x04, info)
    t.w32(this + 0x08, rng.choice([0, t.alloc(0x10, "helper")]))
    t.w32(this + 0x0C, src)
    t.w32(this + 0x14, dst)
    t.args(r3=this)
