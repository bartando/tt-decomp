"""Stream configuration list guards, forward overlap and signed callback results."""
import struct
from liftcheck.spec import *


def interval(ctx):
    obj = ctx.r(3)
    ctx.write(obj + 0x100, ctx.read(obj + 0x20, 56))
    ctx.write(obj + 0x138, ctx.read(obj + 0x99, 1))
    if ctx.read(obj + 0xfc, 1) != b'\0':
        ctx.write(obj + 0xb0, ctx.read(obj + 0xfd, 2))
    ctx.ret(r3=struct.unpack('>I', ctx.read(obj + 0xf0, 4))[0])


CALLS = {'stream.vfn_16': model(interval, args=('r3', 'f1')),
         'phStream_Configure': run(), 'phStream_ConfigurePrimary': run(),
         'phStream_ConfigurePacked': run()}


def inputs(t):
    obj = t.alloc(0x180, 'streamAndGuards') + 32
    t.w32(obj, t.vtable('stream', 19))
    t.w8(obj + 0xfc, 0)
    link = t.alloc(16, 'listLink')
    other = t.alloc(16, 'otherListLink')
    t.w32(obj + 4, t.pick((obj + 4, link, 0)))
    t.w32(obj + 0xc, t.pick((link, other, 0)))
    flags = t.pick((0, 1, 2, 0x80, 0xff))
    t.w8(obj + 0x98, flags)
    t.w32(obj + 0xf0, t.pick((0, 1, 7, 0x7fffffff, -1, -4, 0x80000000)))
    source = t.alloc(80, 'configurationAndGuards') + 12
    if t.index % 3 == 0:
        source = obj + t.pick((0x10, 0x1c, 0x20, 0x24, 0x30, 0x60))
    if flags & 1:
        source = 0
    t.args(r3=obj, r4=source, r5=t.u32())
    return obj
