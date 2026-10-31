"""Joint count/state virtuals, flattened output arrays and observable store ordering."""
import struct
from liftcheck.spec import *


def count(ctx):
    obj = ctx.r(3)
    number = struct.unpack('>i', ctx.read(obj + 4, 4))[0]
    slot, replacement, count_slot = struct.unpack('>III', ctx.read(obj + 12, 12))
    if replacement:
        ctx.write(slot, struct.pack('>I', replacement))
    if count_slot:
        ctx.write(count_slot, bytes(4))
    ctx.ret(number)


def state(ctx):
    obj, axis = ctx.r(3), ctx.r(4)
    owners, first = struct.unpack('>II', ctx.read(obj + 24, 8))
    # Record what the virtual observes before its outputs are written.
    ctx.write(obj + 0x30 + axis * 4, ctx.read(owners + (first + axis) * 4, 4))
    record = ctx.read(obj + 0x50 + axis * 20, 20)
    for register, offset in ((5, 0), (6, 4), (7, 8), (8, 12), (9, 16)):
        ctx.write(ctx.r(register), record[offset:offset + 4])
    ctx.ret()


CALLS = {}
for i in range(6):
    for prefix in ('limitJoint', 'limitReplacement'):
        CALLS[f'{prefix}{i}.vfn_3'] = model(count, args=('r3',))
        CALLS[f'{prefix}{i}.vfn_4'] = model(state, args=('r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9'))


def inputs(t):
    n = t.rng.choice((-3, 0, 1, 2, 4, 7))
    data = t.alloc(0x240, 'jointDataAndGuards')
    t.w32(data + 4, n)
    owners = t.alloc(160, 'jointIndicesAndGuards') + 16
    states = t.alloc(160, 'statesAndGuards') + 16
    errors = t.alloc(160, 'errorsAndGuards', floats=[(16, 32)]) + 16
    references = t.alloc(160, 'referenceErrorsAndGuards', floats=[(16, 32)]) + 16
    weights = t.alloc(160, 'weightsAndGuards', floats=[(16, 32)]) + 16
    if t.index % 7 == 0:
        states = owners
    if t.index % 5 == 0:
        references, weights = errors, errors + 4
    first = 0
    for i in range(max(0, n - 1)):
        number = t.rng.choice((-2, 0, 1, 2, 4))
        objects = []
        for prefix in ('limitJoint', 'limitReplacement'):
            obj = t.alloc(0xB0, f'{prefix}{i}')
            objects.append(obj)
            t.w32(obj, t.vtable(f'{prefix}{i}', 5))
            t.w32(obj + 4, number)
            t.w32(obj + 12, data + 0xA8 + i * 4)
            t.w32(obj + 16, 0)
            t.w32(obj + 20, data + 4 if t.index % 4 == 0 else 0)
            t.w32(obj + 24, owners)
            t.w32(obj + 28, first)
            for axis in range(max(0, number)):
                record = obj + 0x50 + axis * 20
                t.w32(record, t.rng.getrandbits(32))
                special = (-0.0, 0.0, 2.0**-149, -2.0**-149, -1.0, 1.0,
                           float('inf'), -float('inf'), float('nan'))
                for field in range(4):
                    value = (t.rng.choice(special) if (t.index + axis) % 3 == 0
                             else t.rng.uniform(-10, 10))
                    t.wf32(record + 4 + field * 4, value)
        t.w32(data + 0xA8 + i * 4, objects[0])
        if t.index % 2:
            t.w32(objects[0] + 16, objects[1])
        first += max(0, number)
    if n <= 1 and t.index % 3 == 0:
        owners = states = errors = references = weights = 0
    t.args(r3=data, r4=owners, r5=states, r6=errors, r7=references, r8=weights)
    return data, (owners, states, errors, references, weights)
