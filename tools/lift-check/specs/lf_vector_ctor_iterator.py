"""0x820C0170: constructor(dst), count times, advancing by signed byte stride.

Nonpositive count with null ctor, repeated destination (stride 0), forward and
reverse traversal, callback effects, and untouched guards. No ignored bytes.
"""
import struct
from liftcheck.spec import *
FUNCTION = 'phJoint3Dof_0170_g'
ADDRESS = 0x820C0170
SOURCE = 'src/physics/ph_update_object.cpp'
TRIALS = 400


def construct(ctx):
    value = int.from_bytes(ctx.read(ctx.r(3), 4), 'big')
    ctx.write(ctx.r(3), struct.pack('>I', (value + 1) & 0xffffffff))
    ctx.ret()


CALLS = {'ctor': model(construct, args=('r3',))}


def inputs(t):
    count = t.rng.choice((-3, 0, 1, 4, 8))
    stride = t.rng.choice((0, 16, 64, 144, -64))
    spacing = max(abs(stride), 16)
    array = t.alloc(spacing * (max(count, 1) + 2) + 32, 'arrayAndGuards')
    start = array + spacing + 16
    if stride < 0 and count > 0:
        start += (count - 1) * spacing
    callback = t.fake_fn('ctor') if count > 0 else 0
    t.args(r3=start, r4=stride, r5=count, r6=callback)
