"""Query/allocate/append, finalization, thread tracking and reentrant state changes."""
from liftcheck.spec import *
FUNCTION = 'rage_A980'
ADDRESS = 0x8235A980
SOURCE = 'src/graphics/grc_command_stream.cpp'
TRIALS = 900
_state = {}


def boundary(ctx, name):
    ctx.rec.derefs['device'] = (ctx.read(_state['device'], 0x3700), None)
    ctx.rec.derefs['tracking'] = (ctx.read(0x8260663C, 4), None)
    for address, data in _state['effects'].get(name, []):
        ctx.write(address, data)


def query(ctx):
    boundary(ctx, 'query')
    _state[ctx.side] = (ctx.r(4), ctx.r(5))
    ctx.write(ctx.r(4), _state['count'].to_bytes(4, 'big'))
    ctx.write(ctx.r(5), _state['source'].to_bytes(4, 'big'))


def allocate(ctx):
    boundary(ctx, 'allocate')
    count, source = _state[ctx.side]
    ctx.write(count, _state['updatedCount'].to_bytes(4, 'big'))
    ctx.write(source, _state['updatedSource'].to_bytes(4, 'big'))
    ctx.ret(r3=_state['block'])


def retire(ctx):
    boundary(ctx, 'retire')
    ctx.rec.derefs['handle'] = (ctx.read(ctx.r(4), 4), None)
    ctx.write(ctx.r(4), _state['updatedCount'].to_bytes(4, 'big'))


CALLS = {
    'rage_A4E0': model(query, args=('r3',)),
    'grcDevice_AllocateCommandData': model(allocate, args=('r3', 'r4', 'r5')),
    'rage_A8C0': model(lambda ctx: boundary(ctx, 'append'), args=('r3', 'r4', 'r5', 'r6', 'r7', 'r8')),
    'rage_A780': model(lambda ctx: boundary(ctx, 'finalize'), args=('r3',)),
    'xe_GetCurrentThreadId': model(lambda ctx: (boundary(ctx, 'thread'), ctx.ret(r3=7)), args=()),
    'rage_AA78': model(retire, args=('r3',)),
}


def inputs(t):
    r = t.rng
    device = t.alloc(0x3800, 'device')
    _state.clear()
    _state['device'] = device
    _state['effects'] = {}
    _state['source'] = r.choice([0, 0, 1, t.u32()])
    _state['count'] = t.u32()
    _state['updatedCount'] = t.u32()
    _state['updatedSource'] = t.u32()
    _state['block'] = r.choice([0, t.alloc(32, 'commands')])
    t.w32(device, t.alloc(32, 'initial cursor'))
    t.w32(device + 0x34E0, r.choice([0, 0, 1, t.u32()]))
    t.w8(device + 0x28C0, r.choice([0, 1, 2, 0x7F, 0x80, 0xFF, r.randrange(256)]))
    t.w8(device + 0x28C1, r.choice([0, 0, 4, 0x80, r.randrange(256)]))
    t.w32(device + 0x289C, r.choice([0, 1, 2, 3, t.u32()]))
    t.w32(0x8260663C, r.choice([0, 1, 2, 0x80000000]))
    for name in ['allocate', 'append', 'finalize', 'thread', 'retire']:
        effects = []
        if r.randrange(2):
            effects += [(device + 0x28C0, bytes([r.choice([0, 1, 2, 0x80, 0xFF])])),
                        (device + 0x28C1, bytes([r.randrange(256)])),
                        (device + 0x289C, r.choice([1, 2, 3, t.u32()]).to_bytes(4, 'big')),
                        (device, t.alloc(32, f'cursor after {name}').to_bytes(4, 'big')),
                        (0x8260663C, r.choice([0, 1, 255]).to_bytes(4, 'big'))]
        _state['effects'][name] = effects
    t.args(r3=device)
