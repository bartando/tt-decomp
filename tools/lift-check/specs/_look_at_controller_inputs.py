"""Look-at driver enable gates, live replacement and target payload observation."""
import struct
from liftcheck.spec import *


def enabled(ctx):
    obj = ctx.r(3)
    owner, replacement, result = struct.unpack('>III', ctx.read(obj + 4, 12))
    ctx.write(owner + 0x34, struct.pack('>I', replacement))
    ctx.ret(r3=result)


CALLS = {}
for name in ('lookDriver', 'replacementDriver'):
    CALLS[f'{name}.vfn_8'] = model(enabled, args=('r3',))
    CALLS[f'{name}.vfn_3'] = stub(ret='void', args=('r3', 'r4'), deref={'r4': 16})
    CALLS[f'{name}.vfn_4'] = stub(ret='void', args=('r3', 'r4', 'r5'), deref={'r4': 16})


def inputs(t):
    obj = t.alloc(0x70, 'controllerAndGuards') + 16
    drivers = []
    for name in ('lookDriver', 'replacementDriver'):
        driver = t.alloc(32, name)
        t.w32(driver, t.vtable(name, 9))
        t.w32(driver + 4, obj)
        t.w32(driver + 12, t.pick((0, 1, 0x100, 0x101, 0x80000000, 0xffffffff, t.u32())))
        drivers.append(driver)
    for driver in drivers:
        t.w32(driver + 8, t.pick(drivers))
    t.w32(obj + 0x34, drivers[0])
    target = t.pick((obj + 0x10, t.alloc(16, 'target')))
    t.args(r3=obj, r4=target, r5=t.pick((-1, 0, 1, 2, 0x12345678)))
