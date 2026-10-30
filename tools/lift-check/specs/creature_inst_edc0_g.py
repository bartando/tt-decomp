"""0x820DEDC0 composes a bone's affine transform with its parent matrix.

The three basis rows use 3-wide dot products; translation uses (src.xyz, 1).
Each output row's fourth lane comes from that destination row's OLD FIRST
lane, an artifact of the final vmrghw sequence, not an affine 0/0/0/1 column.
There are no calls or vtable accesses (the pongCreatureInst name is misleading).

Coverage: independent buffers, identity/zero/non-affine matrices, arbitrary
fourth lanes, exact and partial aliasing, including all three arguments equal.
Limits: valid 16-byte-aligned 64-byte matrices and finite ordinary floats;
no NaN/Inf/denormal or invalid-pointer behavior. All output lanes are compared
exactly against lift-check's VMX dot-product model (not physical Xenon hardware).
The normal boot static initializers supply the xyz mask and homogeneous one.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "pongCreatureInst_EDC0_g"
ADDRESS = 0x820DEDC0
SOURCE = "src/game/creature/pong_creature.cpp"


def inputs(t):
    rng = t.rng
    blocks = [t.alloc(0x80, name) for name in ("dst", "bone", "parent")]
    for base in blocks:
        t.floats(base, 32, -8.0, 8.0)

    dst, bone, parent = blocks
    mode = rng.randrange(9)
    if mode == 1:
        dst = bone
    elif mode == 2:
        dst = parent
    elif mode == 3:
        parent = bone
    elif mode == 4:
        dst = parent = bone
    elif mode == 5:
        dst = bone + 0x10
    elif mode == 6:
        bone = dst + 0x20
    elif mode == 7:
        dst = parent + 0x30
    elif mode == 8:
        parent = dst + 0x10

    # Keep every combination reachable, including affine and non-affine data.
    for base in (bone, parent):
        kind = rng.randrange(5)
        if kind < 2:
            for row in range(4):
                for col in range(4):
                    t.wf32(base + 16 * row + 4 * col,
                           float(row == col) if kind == 0 else 0.0)
        elif kind == 2:
            for row in range(4):
                t.wf32(base + 16 * row + 12, float(row == 3))

    # Keep the vmrghw leftovers bit-for-bit even with a CLI FTOL override.
    for row in range(4):
        t.float_words.discard(dst + 16 * row + 12)
    t.args(r3=dst, r4=bone, r5=parent)
