"""Chain links, allocation/fallback branches, imported device indirection and
callback-visible publication order. The cache helper preserves r7 in .text.s."""
from liftcheck.spec import *
FUNCTION = 'grc_9B60'
ADDRESS = 0x82359B60
SOURCE = 'src/graphics/grc_command_stream.cpp'
TRIALS = 700
_state = {}


def snapshot(ctx):
    ctx.rec.derefs['state'] = (b''.join(ctx.read(a, n) for a, n in _state['ranges']), None)


def allocate(ctx):
    snapshot(ctx)
    for address, data in _state['effects']:
        ctx.write(address, data)
    ctx.ret(r3=_state['block'])


CALLS = {
    'grcDevice_AllocateCommandData': model(allocate, args=('r3', 'r4', 'r5')),
    'KeGetCurrentProcessType': model(lambda ctx: (snapshot(ctx), ctx.ret(r3=_state['process'])), args=()),
    'rage_EEC0': model(snapshot, args=('r3', 'r4'), preserves=('r7',)),
}


def inputs(t):
    r = t.rng
    queue = t.alloc(32, 'queue')
    device = t.alloc(32, 'allocation device')
    blocks = [t.alloc(0x1080, f'block{i}') for i in range(4)]
    aperture = t.map(r.choice([0xDFFF8000, 0xE0000000, 0xE1000000]), 0x4000, 'GPU aperture')
    if r.randrange(2):
        blocks[0], blocks[1] = aperture + 0x80, aperture + 0x2000
    cursor = r.choice([0, blocks[0] + 4, blocks[0] + 20])
    tail = r.choice([0, blocks[0], cursor])
    t.w32(queue + 4, tail)
    t.w32(queue + 8, cursor)
    t.w32(queue + 16, device)
    for i, imported in enumerate([0x82000730, 0x82000734]):
        slot = t.alloc(4, f'import slot{i}')
        gpu = t.alloc(0x3D20, f'GPU{i}')
        t.w32(imported, slot)
        t.w32(slot, gpu)
        t.w32(gpu + 0x3D1C, blocks[2 + i])
    _state['block'] = r.choice([0, 0, blocks[1]])
    _state['process'] = r.choice([0, 1, 2, 3, 0xFFFFFFFF])
    _state['ranges'] = [(queue, 20), (blocks[0], 32), (blocks[1], 32)]
    # Allocation can move the chain cursor: the helper must reload it.
    _state['effects'] = [(queue + 8, r.choice([0, cursor, blocks[0] + 12]).to_bytes(4, 'big'))]
    t.args(r3=queue)
