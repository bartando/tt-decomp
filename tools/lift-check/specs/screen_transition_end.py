"""Callback sees both old slots; reset reads the possibly modified template after it."""
from liftcheck.spec import *
FUNCTION = 'pongScrnTransFadeIn_EndTransition'
ADDRESS = 0x82378460
SOURCE = 'src/game/pong_render.cpp'
TRIALS = 1000
_state = {}


def callback(ctx):
    ctx.rec.derefs['callbacks'] = (ctx.read(ctx.r(3) - 16, 32), None)
    for address, data in _state['effects']:
        ctx.write(address, data)


CALLS = {'sysCallback_Invoke': model(callback, args=('r3', 'r4'))}


def inputs(t):
    r = t.rng
    transition = t.alloc(0x80, 'transition')
    t.w32(transition + 0x2C, r.choice([0, 0, 1, 2, 4, 0x80000000, 0xFFFFFFFF]))
    template = 0x8261A0C0
    t.put(template, r.randbytes(16))
    _state['effects'] = []
    if r.randrange(2):
        _state['effects'].append((template, r.randbytes(16)))
    if r.randrange(2):
        _state['effects'].append((transition + 0x10, r.randbytes(32)))
    t.args(r3=transition)
