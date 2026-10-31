"""Virtual record query, pointer output and signed error propagation."""
import struct
from liftcheck.spec import *


def record(ctx):
    obj = ctx.r(3)
    ctx.write(ctx.r(4), ctx.read(obj + 0xf4, 4))
    ctx.ret(r3=struct.unpack('>I', ctx.read(obj + 0xf0, 4))[0])


CALLS = {'recordStream.vfn_18': model(record, args=('r3', 'r4')),
         'phStream_GetRecordField': run()}


def inputs(t):
    owner = t.alloc(0x180, 'ownerAndGuards') + 16
    stream = owner + 0x10
    t.w32(stream, t.vtable('recordStream', 19))
    value = t.alloc(32, 'record')
    status = t.pick((0, 1, 7, -1, -4, 0x80000000))
    t.w32(stream + 0xf0, status)
    t.w32(stream + 0xf4, value if status >= 0 and status < 0x80000000 else 0)
    output = t.alloc(32, 'outputAndGuards') + 12
    if t.index % 5 == 0:
        output = value + 0x10
    t.args(r3=owner, r4=output)
    return owner
