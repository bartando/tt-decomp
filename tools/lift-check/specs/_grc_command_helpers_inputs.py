"""Boundary snapshots include the device and packet buffers; no ignored ranges.
Models change state and escaped query outputs to test reload/capture ordering."""
from liftcheck.spec import model
from liftcheck.abi import wide_return
_state = {}


def atomic_return(ctx, value):
    if wide_return(ctx.sig):
        ctx.ret(r3=value)
    else:
        ctx.ret(r3=value >> 32)
        ctx.m.set_gpr(4, value & 0xFFFFFFFF)


def atomic_load(ctx):
    atomic_return(ctx, int.from_bytes(ctx.read(ctx.m.gpr(3), 8), 'big'))


def atomic_exchange(ctx):
    pointer = ctx.m.gpr(3)
    previous = int.from_bytes(ctx.read(pointer, 8), 'big')
    replacement = (ctx.m.gpr(5) << 32) | ctx.m.gpr(6)
    ctx.write(pointer, replacement.to_bytes(8, 'big'))
    atomic_return(ctx, previous)


# PPC32 lowers native 64-bit atomics to compiler-runtime helpers. These models
# provide their ABI, while the original executes its real ld/ldarx/stdcx loop.
HOST = {
    '__atomic_load_8': model(atomic_load, transparent=True, args=(), preserves=('r4',)),
    '__atomic_exchange_8': model(atomic_exchange, transparent=True, args=(), preserves=('r4',)),
}


def word(value):
    return (value & 0xFFFFFFFF).to_bytes(4, 'big')


def snapshot(ctx, name):
    ctx.rec.derefs['state'] = (b''.join(ctx.read(a, n) for a, n in _state['ranges']), None)
    for address, data in _state['effects'].get(name, []):
        ctx.write(address, data)


def query(ctx):
    snapshot(ctx, 'query')
    _state['outputs'][ctx.side] = (ctx.r(4), ctx.r(5))
    ctx.write(ctx.r(4), word(_state['gpuAddress']))
    ctx.write(ctx.r(5), word(_state['wordCount']))


def allocate(ctx):
    snapshot(ctx, 'allocate')
    # The real allocator returns before its callback when the fallback bit is set.
    if ctx.read(_state['device'] + 0x28C1, 1)[0] & 0x80:
        ctx.ret(r3=0)
        return
    count = _state['allocationCalls'].get(ctx.side, 0)
    _state['allocationCalls'][ctx.side] = count + 1
    for address, data in _state['allocationEffects']:
        ctx.write(address, data)
    if ctx.side in _state['outputs']:
        address, words = _state['outputs'][ctx.side]
        ctx.write(address, word(_state['updatedAddress']))
        ctx.write(words, word(_state['updatedWords']))
    ctx.ret(r3=_state['allocations'][min(count, 1)])


def acquire(ctx):
    snapshot(ctx, 'lock')
    ctx.ret(r3=_state['irql'])


def linked(ctx):
    snapshot(ctx, 'linked')
    ctx.ret(r3=_state['buffers'][2] + 64)


def append(ctx):
    snapshot(ctx, 'append')
    ctx.ret(r3=_state['buffers'][3] + 32)


def refill(ctx):
    snapshot(ctx, 'refill')
    ctx.ret(r3=_state['buffers'][4])


def grow(ctx):
    snapshot(ctx, 'grow')
    ctx.ret(r3=_state['buffers'][3])


def fence(ctx):
    snapshot(ctx, 'fence')
    ctx.ret(r3=ctx.r(4) + 32)


def clip(ctx):
    ctx.rec.derefs['plane'] = (ctx.read(ctx.r(5), 16), None)
    snapshot(ctx, 'clip')


def trailer(ctx):
    snapshot(ctx, 'trailer')
    ctx.ret(r3=ctx.r(4) + 128)


CALLS = {
    'grcDevice_AllocateCommandData': model(allocate, args=('r3', 'r4', 'r5')),
    'rage_A4E0': model(query, args=('r3',)),
    'KfAcquireSpinLock': model(acquire, args=('r3',)),
    'KfReleaseSpinLock': model(lambda ctx: snapshot(ctx, 'unlock'), args=('r3', 'r4')),
    'rage_9C88': model(linked, args=('r3', 'r4', 'r5', 'r6')),
    'phInst_A340_p42': model(lambda ctx: (snapshot(ctx, 'direct'),
        ctx.rec.derefs.update(packet=(ctx.read(ctx.r(4), 8), None))), args=('r3', 'r5')),
    'grc_9B60': model(grow, args=('r3',)),
    'phInst_A6A8_p42': model(fence, args=('r3', 'r4')),
    'rage_A8C0': model(append, args=('r3', 'r4', 'r5', 'r6', 'r7', 'r8')),
    'rage_A150': model(lambda ctx: snapshot(ctx, 'reserve'), args=('r3', 'r4')),
    'rage_A980': model(refill, args=('r3',)),
    'grc_5E08': model(lambda ctx: snapshot(ctx, 'viewport'), args=('r3', 'r4')),
    'rage_6858': model(clip, args=('r3', 'r4')),
    'phInst_AB60_v12': model(trailer, args=('r3', 'r4', 'r5', 'r6', 'r7')),
}


def inputs(t, which):
    r = t.rng
    _state.clear()
    device = t.alloc(0x5100, 'device')
    buffers = [t.alloc(1024, f'commands{i}') for i in range(6)]
    if t.index % 3 == 0:
        buffers[1] = t.map(0xE1000000, 4096, 'GPU packet aperture')
    _state.update(device=device, buffers=buffers, outputs={}, allocationCalls={}, effects={})
    _state['ranges'] = [(device, 0x5100)] + [(a, 1024) for a in buffers]
    _state['allocations'] = [r.choice([0, buffers[1]]), r.choice([0, buffers[2]])]
    _state['gpuAddress'] = r.choice([0, buffers[5], t.u32()])
    _state['wordCount'] = r.choice([0, 0, 1, 22, t.u32()])
    _state['updatedAddress'], _state['updatedWords'] = t.u32(), t.u32()
    _state['irql'] = r.randrange(256)
    _state['allocationEffects'] = []
    initial_mode = r.choice([0, 0, 4, 0x80, 0x84, 0xFF])
    t.w8(device + 0x28C0, r.choice([0, 1, 0x80, 0xFF]))
    t.w8(device + 0x28C1, initial_mode)
    t.w8(device + 0x28C2, r.choice([0, 1, 0x10, 0xFF]))
    pending = r.choice([0xFFFFFFFF, 0xFFFFFFFF, r.getrandbits(64), 0, 0xFFFFFFFF00000000])
    t.w64(device + 0x2C98, pending)
    t.w32(device, buffers[0] + r.choice([0, 4, 32, 96]))
    t.w32(device + 8, buffers[0] + r.choice([0, 32, 128, 256]))
    t.w32(device + 0x36CC, buffers[0] + r.choice([0, 4, 64, 100]))
    t.w32(device + 0x34E0, r.choice([0, 0, 1, t.u32()]))
    t.w32(device + 0x4FE0, r.choice([0, t.alloc(16, 'submission owner')]))
    t.w32(device + 0x28FC, r.choice([0, 0, 1, 2, 0xFFFFFFFF]))
    t.w32(device + 0x36B4, r.choice([0xE0000001, 0xDFFFFFFF, t.u32()]))
    t.w32(device + 0x36B8, r.choice([0, 0xFFFFFFFF, 0xE1000123, t.u32()]))
    for i, offset in enumerate([0x34F0, 0x3504, 0x3518]):
        t.w32(device + offset, buffers[i] + 128)
        t.w32(device + offset + 4, buffers[i] + 256)
        t.w32(device + offset + 8, buffers[i] + 272)
        t.w32(device + offset + 12, buffers[i] + r.choice([272, 280, 288]))
    for i in range(24):
        t.wf32(device + 0x3230 + i * 4, r.uniform(-20, 20))
    # Ordinary callbacks can replace these values. Never expose the original's
    # uninitialized query locals by clearing fallback mode before any query.
    for name in ['lock', 'linked', 'unlock', 'append', 'fence', 'grow', 'refill', 'viewport', 'clip', 'trailer']:
        effects = []
        if r.randrange(2):
            effects += [(device + 0x28FC, word(r.choice([0, 1, 2, 0xFFFFFFFF])))]
        if name in ['append', 'fence', 'grow', 'refill', 'clip'] and r.randrange(2):
            effects += [(device, word(buffers[4] + 16)), (device + 8, word(buffers[4] + r.choice([0, 128]))),
                        (device + 0x36C0, word(r.choice([0, 1, 4095, 0xFFFFFFFF])))]
        _state['effects'][name] = effects
    if which == 'query':
        # The allocation callback can replace the atomic range after the gate.
        if r.randrange(2):
            _state['allocationEffects'] = [(device + 0x2C98, r.getrandbits(64).to_bytes(8, 'big')),
                                            (device + 0x28C2, bytes([r.randrange(256)]))]
        output = t.alloc(16, 'query outputs')
        t.args(r3=device, r4=output, r5=output + 4)
    elif which == 'append':
        t.args(r3=device, r4=buffers[0], r5=t.u32(), r6=t.u32(),
               r7=r.choice([0, 1, 2, 0xFFFFFFFF]), r8=device + 0x3504)
    elif which == 'reset':
        t.w32(device + 0x32A0, r.choice([0, 1, 0xFFFFFFFF, t.u32()]))
        t.args(r3=device, r4=r.choice([0, 1, 2, 3, 4, 0xFFFFFFFF, t.u32()]))
    elif which == 'submit':
        t.args(r3=device, r4=r.choice([0, 1, 2, 3, 0xFFFFFFFF]), r5=t.u32())
    else:
        t.args(r3=device)
