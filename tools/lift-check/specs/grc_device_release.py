"""Count wrap, last-reference teardown, header reload and tagged allocation free."""
from liftcheck.spec import *
FUNCTION = 'grcDevice_Release'
ADDRESS = 0x8235EAD8
SOURCE = 'src/graphics/grc_device.cpp'
TRIALS = 800
_state = {}


def boundary(ctx):
    ctx.rec.derefs['device'] = (ctx.read(_state['device'] - 4, 36), None)


def teardown(ctx):
    boundary(ctx)
    for address, data in _state['effects']:
        ctx.write(address, data)


CALLS = {
    'grcDeviceXenon_teardown': model(teardown, args=('r3',)),
    '_locale_register': model(boundary, args=('r3', 'r4')),
}


def inputs(t):
    r = t.rng
    device = t.alloc(64, 'deviceAndHeader') + 16
    original = t.alloc(16, 'allocation')
    changed = t.alloc(16, 'replacement allocation')
    _state['device'] = device
    _state['effects'] = []
    t.w32(device - 4, original)
    t.w32(device + 12, r.choice([0, 1, 1, 1, 2, 3, 0x80000000, 0xFFFFFFFF, t.u32()]))
    if r.randrange(2):
        _state['effects'] = [(device - 4, changed.to_bytes(4, 'big')),
                             (device + 12, t.u32().to_bytes(4, 'big'))]
    t.args(r3=device)
