"""Resource virtual, null fallback, counter publication and table reload ordering."""
from liftcheck.spec import *
FUNCTION = 'pongShadowMap_A5C8_g'
ADDRESS = 0x8215A5C8
SOURCE = 'src/game/pong_render.cpp'
TRIALS = 1200
_state = {}


def resource(ctx):
    assert int.from_bytes(ctx.read(0x825EBC54, 4), 'big') == _state['incremented'], 'counter before virtual'
    for addr, data in _state['effects']:
        ctx.write(addr, data)
    ctx.ret(r3=_state['resource'])


CALLS = {'texture.vfn_20': model(resource, args=('r3',))}


def inputs(t):
    r = t.rng
    vt = t.vtable('texture', slots=26)
    texture = t.alloc(32, 'texture')
    fallback = t.alloc(32, 'fallback')
    t.w32(texture, vt)
    t.w32(fallback, vt)
    tables = []
    for i in range(2):
        table = t.alloc(0x120, f'table{i}')
        entries = t.alloc(128, f'entries{i}')
        bank = t.alloc(1024, f'bank{i}')
        t.w32(table + 0x100, entries)
        t.w32(table + 0x108, bank)
        for j in range(8):
            t.w32(entries + j * 8 + 4, (t.u32() & 0xFFFF0000) | r.randrange(64))
        tables.append(table)
    counter = r.choice([0, 0xFFFFFFFF, t.u32()])
    t.w32(0x825EBC40, tables[0])
    t.w32(0x825EBC54, counter)
    t.w32(0x825EBA20, fallback)
    _state['incremented'] = (counter + 1) & 0xFFFFFFFF
    _state['resource'] = r.choice([0, t.alloc(16, 'resource')])
    _state['effects'] = [(0x825EBC40, tables[r.randrange(2)].to_bytes(4, 'big')),
                         (0x825EBC54, t.u32().to_bytes(4, 'big'))]
    bit = r.choice([0, 1, 7, 8, 15, 2047, r.randrange(2048)])
    t.args(r3=(r.randrange(8) << 18) | (bit << 1) | r.randrange(2),
           r4=r.choice([0, texture]))
