from liftcheck.spec import *

_parents = {}
_mutate = False
_holder = 0
_replacement = 0
_slots = (0x825EBA0C, 0x825EBA08, 0x825EB984, 0x825EB9E0)
_pool = []


def resource(t, depth=0):
    p = t.alloc(80, 'resourceAndGuards') + 16
    flags = t.u32() & ~(255 | 0x70000 | 0xF80000)
    flags |= t.rng.choice([0, 1, 1, 2, 255])
    flags |= t.rng.choice([0, 1, 4, 4, 7]) << 16
    flags |= t.rng.choice([0, 0, 1, 31]) << 19
    t.w32(p, flags)
    linked = resource(t, depth - 1) if depth else 0
    t.w32(p + 0x2C, linked)
    if linked: _parents[linked] = p
    return p


def texture_release(c):
    p = c.r(3)
    c.rec.derefs['r3'] = (c.read(p, 48), None)
    if _mutate and p in _parents:
        parent = _parents[p]
        flags = int.from_bytes(c.read(parent, 4), 'big') | 0x80000
        c.write(parent, flags.to_bytes(4, 'big'))
    c.ret()

RESOURCE_CALLS = {'grcTexture_ReleaseResource': model(texture_release, args=('r3',))}


def resource_input(t):
    global _parents, _mutate
    _parents = {}
    _mutate = t.index % 3 == 0
    t.args(r3=resource(t, t.rng.randrange(4)))


def holder_callback(c):
    c.write(_holder, _replacement.to_bytes(4, 'big'))
    c.ret()

HOLDER_CALLS = {
    0x820C02D0: model(holder_callback, args=('r3', 'r4')),
    0x8258662C: model(holder_callback, args=()),
}


def holder_input(t):
    global _holder, _replacement
    _holder = t.alloc(32, 'holderAndGuards') + 8
    _replacement = t.alloc(32, 'reentrantReplacement')
    p = t.alloc(32, 'allocation') if t.rng.randrange(4) else 0
    if p: t.w32(p + 4, t.rng.choice([0, 1, 1, 2, 0xffffffff, t.u32()]))
    t.w32(_holder, p)
    t.args(r3=_holder)


def change_slots(c):
    if _mutate:
        slot = c.rng.choice(_slots)
        pointer = c.rng.choice([0] + _pool)
        c.write(slot, pointer.to_bytes(4, 'big'))


def shared_release(c):
    c.rec.derefs['r3'] = (c.read(c.r(3), 16) + b''.join(c.read(p, 4) for p in _slots), None)
    change_slots(c)
    c.ret(r3=c.rng.choice([0, 0, 1, 0xffffffff]))


def shared_debug(c):
    change_slots(c)
    c.ret()

SHARED_CALLS = {
    'grcResource_ReleaseRef': model(shared_release, args=('r3',)),
    0x8258662C: model(shared_debug, args=()),
}


def shared_input(t):
    global _mutate, _pool
    _mutate = t.index % 3 == 0
    _pool = [t.alloc(64, 'sharedResource') for _ in range(4)]
    for slot in _slots: t.w32(slot, t.rng.choice([0] + _pool))
