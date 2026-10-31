"""Inclusive fixup-space boundary, 6-bit shifts, error result and callback ordering."""
from liftcheck.spec import *
FUNCTION = 'rage_C660'
ADDRESS = 0x8235C660
SOURCE = 'src/graphics/grc_command_stream.cpp'
TRIALS = 900
_state = {}


def boundary(ctx, name):
    ctx.rec.derefs['state'] = (ctx.read(_state['device'], 0x3700), None)
    ctx.rec.derefs['commands'] = (b''.join(ctx.read(a, 32) for a in _state['buffers']), None)
    for address, data in _state['effects'].get(name, []):
        ctx.write(address, data)


CALLS = {
    'rage_A980': model(lambda ctx: (boundary(ctx, 'refill'), ctx.ret(r3=_state['buffers'][0])), args=('r3',)),
    'grc_9B60': model(lambda ctx: (boundary(ctx, 'grow'), ctx.ret(r3=_state['buffers'][1])), args=('r3',)),
    'rage_7BD0': model(lambda ctx: (boundary(ctx, 'submit'), ctx.ret(r3=_state['error'])), args=('r3', 'r4', 'r5')),
    'rage_35A8': model(lambda ctx: boundary(ctx, 'reset'), args=('r3', 'r4')),
}


def inputs(t):
    r = t.rng
    device = t.alloc(0x3800, 'device')
    buffers = [t.alloc(64, f'commands{i}') for i in range(2)]
    _state['device'], _state['buffers'] = device, buffers
    _state['error'] = r.choice([0, 0, 1, 2, 0xFFFFFFFF])
    _state['effects'] = {}
    t.w8(device + 0x28C0, r.choice([0, 1, 2, 3, 0x10, 0xFF, r.randrange(256)]))
    t.w32(device + 0x350C, buffers[0])
    t.w32(device + 0x3510, buffers[0] + r.choice([0, 4, 8]))
    t.w32(device + 0x2B38, r.choice([0, 1, 7, 8, 31, 32, 33, 63, 64, 0xFFFFFFFF, t.u32()]))
    for name in ['refill', 'grow', 'submit', 'reset']:
        effects = []
        if r.randrange(2):
            effects.append((device + 0x28C0, bytes([r.choice([0, 1, 2, 0x10, 0xFF, r.randrange(256)])])))
        if name == 'refill' and r.randrange(2):
            effects += [(device + 0x350C, (buffers[0] + 8).to_bytes(4, 'big')),
                        (device + 0x3510, (buffers[0] + r.choice([8, 12, 16])).to_bytes(4, 'big'))]
        _state['effects'][name] = effects
    t.args(r3=device)
