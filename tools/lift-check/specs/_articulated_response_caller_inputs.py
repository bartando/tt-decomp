"""Bone resolution replaces joint data, proving callers reload its confirmed slot."""
import struct
from liftcheck.spec import *
from specs._articulated_single_response_inputs import tree, vector


def resolve(ctx):
    replacement, index = struct.unpack('>II', ctx.read(ctx.r(3) + 0x200, 8))
    ctx.write(ctx.r(3) + 0x1D0, struct.pack('>I', replacement))
    ctx.ret(index)


RESOLVE = model(resolve, args=('r3', 'r4'))


def inputs(t):
    data, array, target = tree(t)
    old_data, _, _ = tree(t)
    collider = t.alloc(0x250, 'colliderAndGuards')
    t.floats(collider + 0xD0, 4, -10, 10)
    t.w32(collider + 0x1D0, old_data)
    t.w32(collider + 0x200, data)
    t.w32(collider + 0x204, target)
    point = vector(t, 'target')
    alternate = vector(t, 'alternateTarget') if t.index % 2 else 0
    bone, alternate_bone = t.rng.getrandbits(32), t.rng.getrandbits(32)
    t.args(r3=collider, r4=bone, r5=point)
    return point, alternate, bone, alternate_bone
