from liftcheck.spec import *


def refill(c):
    device = c.r(3)
    c.rec.derefs['r3'] = (c.read(device, 0x40) + c.read(device + 0x2CF4, 4)
                         + c.read(device + 0x2D94, 4), None)
    cursor = c.alloc(256)
    c.write(device, cursor.to_bytes(4, 'big'))
    c.write(device + 8, (cursor + 252).to_bytes(4, 'big'))
    # Refill may change the cached source planes; callers must reload them.
    for offset in range(0x3230, 0x3290, 4):
        c.write(device + offset, c.rng.getrandbits(32).to_bytes(4, 'big'))
    c.ret(r3=cursor)

REFILL_CALLS = {'rage_A980': model(refill, args=('r3',))}

def device(t):
    p = t.alloc(0x5400, 'device')
    cursor = t.alloc(256, 'commandStorage') + 16
    t.w32(p, cursor)
    t.w32(p + 8, cursor + t.rng.choice([-4, 0, 4, 64]))
    for offset in (0x20, 0x28, 0x30):
        t.w64(p + offset, t.rng.choice([0, (1 << 64) - 1, t.rng.getrandbits(64)]))
    t.w32(p + 0x32A0, t.rng.choice([0, 1, t.u32()]))
    return p, cursor
