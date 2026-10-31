"""Acyclic joint trees and observable parent/child response virtuals."""
import struct
from liftcheck.spec import *
from specs._articulated_step_inputs import bodies


def response(ctx):
    values = struct.unpack('>8f', ctx.read(ctx.r(4), 32))
    coefficient = struct.unpack('>f', ctx.read(ctx.r(3) + 4, 4))[0]
    result = [(values[lane] + values[(lane + 3) % 8]) * coefficient for lane in range(8)]
    ctx.write(ctx.r(5), struct.pack('>8f', *result))
    ctx.ret()


CALLS = {'phSpatialTensor_Multiply': run()}
for i in range(8):
    for slot in (27, 28):
        CALLS[f'forceJoint{i}.vfn_{slot}'] = model(response, args=('r3', 'r4', 'r5'), deref={'r4': 32})


def inputs(t):
    data, array = bodies(t)
    for i in range(len(array) - 1):
        joint = t.alloc(0x240, f'forceJoint{i}')
        t.w32(joint, t.vtable(f'forceJoint{i}', 29))
        t.wf32(joint + 4, t.rng.choice((0., 0.125, -0.25, 0.5)))
        t.floats(joint + 0x1B0, 16, -10, 10)
        t.w32(data + 0xA8 + 4 * i, joint)
        parent = t.rng.randrange(i + 1) if t.index % 3 else i
        t.w32(data + 0x124 + 4 * i, parent)
    t.args(r3=data)
