"""Continue partial runs across repeated refills, stride rounding and source
aliases. The refill model publishes one cursor and returns another, so the
caller must use the stored cursor. Compare all bytes, headers and final pointer.
Stride is valid/nonzero (1, 6 or 16); malformed dividing inputs are out of scope.
"""
from liftcheck.spec import *
FUNCTION = 'grcDevice_WriteRegisterRunOverflow'
ADDRESS = 0x823625A0
SOURCE = 'src/graphics/grc_state_helpers.cpp'
TRIALS = 800
_stride = 1


def refill(c):
    p = c.r(3)
    c.rec.derefs['r3'] = (c.read(p, 12), None)
    cursor = c.alloc(2048)
    capacity = (_stride * c.rng.choice([1, 2, 3]) + 1) * 4
    c.write(p, cursor.to_bytes(4, 'big'))
    c.write(p + 4, (cursor + capacity).to_bytes(4, 'big'))
    c.ret(r3=cursor + 4)

CALLS = {'rage_A980': model(refill, args=('r3',))}


def inputs(t):
    global _stride
    r = t.rng
    _stride = r.choice([1, 6, 16])
    count = r.choice([0, 1, _stride, _stride + 1, r.randrange(1, 97)])
    p = t.alloc(32, 'device')
    cursor = t.alloc(2048, 'commands') + 16
    source = r.choice([t.alloc((count + 8) * 4, 'source') + 12, cursor, cursor + 16])
    capacity = r.choice([-4, 0, 4, 8, _stride * 4, (_stride + 1) * 4, 512])
    t.w32(p, cursor)
    t.w32(p + 4, cursor + capacity)
    t.args(r3=p, r4=cursor, r5=r.randrange(0x2000, 0x3000), r6=source, r7=count, r8=_stride)
