"""Stream windows, short/error transfers, and reentrant device callbacks.
Invalid windows/negative byte counts are outside the device contract. No memory
is ignored. Device calls observe the complete stream before mutating it.
"""
from liftcheck.spec import *
_s = 0
_alt = 0
_mutate = False
_mutate_cursor = True
_root = 0
_result = 0
_attempt = 0
_success = 0


def observe(c):
    c.rec.derefs['stream'] = (c.read(_s, 28), None)
    if _mutate:
        c.write(_s, _alt.to_bytes(4, 'big'))
        c.write(_s + 4, c.rng.getrandbits(32).to_bytes(4, 'big'))
        c.write(_s + 12, c.rng.getrandbits(32).to_bytes(4, 'big'))
        if _mutate_cursor:
            c.write(_s + 16, c.rng.randrange(16).to_bytes(4, 'big'))


def device_read(c):
    observe(c)
    n = c.r(6)
    got = c.rng.choice([-1, -7, 0, n, c.rng.randrange(n + 1)])
    if got > 0: c.write(c.r(5), c.rng.randbytes(got))
    c.ret(r3=got)


def device_other(c):
    observe(c)
    c.ret(r3=c.rng.choice([-7, -1, 0, 1, 0x12345678]))


CALLS = {'fiStreamBuf_Finalize': run()}
for prefix in ['device', 'replacement']:
    CALLS[prefix + '.vfn_3'] = model(device_read, args=('r3','r4','r5','r6'))
    for slot, args in [(4, ('r3','r4','r5','r6')), (5, ('r3','r4','r5','r6')),
                       (6, ('r3','r4')), (8, ('r3','r4'))]:
        CALLS[prefix + '.vfn_' + str(slot)] = model(device_other, args=args)


def stream(t):
    global _s, _alt, _mutate, _mutate_cursor
    _s = t.alloc(60, 'streamAndGuards') + 16
    device = t.alloc(16, 'device')
    _alt = t.alloc(16, 'replacement')
    t.w32(device, t.vtable('device', slots=9))
    t.w32(_alt, t.vtable('replacement', slots=9))
    buffer = t.alloc(288, 'bufferAndGuards') + 16
    capacity = t.rng.choice([1, 4, 16, 64, 128, 256])
    end = t.rng.choice([0, capacity, t.rng.randrange(capacity + 1)])
    cursor = t.rng.randrange((end or capacity) + 1)
    t.w32(_s, device)
    t.w32(_s + 4, t.u32())
    t.w32(_s + 8, buffer)
    t.w32(_s + 12, t.u32())
    t.w32(_s + 16, cursor)
    t.w32(_s + 20, end)
    t.w32(_s + 24, capacity)
    _mutate = t.index % 3 == 0
    _mutate_cursor = True
    t.args(r3=_s)
    return capacity


def read_input(t):
    global _mutate_cursor
    cap = stream(t)
    _mutate_cursor = False
    dst = t.alloc(1056, 'outputAndGuards') + 16
    t.args(r4=dst, r5=t.rng.choice([0, 1, cap-1, cap, cap+1, t.rng.randrange(1025)]))


def reset_input(t):
    stream(t)
    t.args(r4=t.u32())


def word_read(c):
    n = c.r(5)
    got = c.rng.choice([-1, -2, -7, 0, n, c.rng.randrange(n + 1)])
    if got > 0: c.write(c.r(4), c.rng.randbytes(got))
    c.ret(r3=got)

WORD_CALLS = {'fiStreamBuf_Read': model(word_read, args=('r3','r4','r5'))}
def word_input(t):
    stream(t)
    t.args(r4=t.alloc(1056, 'wordOutputAndGuards') + 16, r5=t.rng.randrange(257))


def build_path(c):
    global _root
    _root = c.r(3)
    c.write(c.r(4), f"root{c.r(8)}/test.ext\0".encode())
    c.ret()

def open_path(c):
    attempt = c.read(c.r(3) + 4, 1)[0] - 48 + 1
    c.write(_root + 0x604, c.rng.choice([-1,0,1,2,4,6]).to_bytes(4, 'big', signed=True))
    c.ret(r3=_result if attempt == _success else 0)

OPEN_CALLS = {'fiPath_Build': model(build_path, args=('r3','r4','r5','r6','r7','r8')),
              'fiStream_Open': model(open_path, args=('r3','r4'))}

def open_input(t):
    global _result, _attempt, _success
    assets = t.alloc(0x610, 'assets')
    _result = t.alloc(28, 'openedStream')
    _attempt = 0
    _success = t.rng.randrange(7)
    t.w32(assets + 0x604, t.rng.choice([-7,-1,0,1,2,4]))
    name = t.alloc(16, 'name', fill=b'test\0' + bytes(11))
    ext = t.alloc(16, 'extension', fill=b'ext\0' + bytes(12))
    t.args(r3=assets,r4=name,r5=ext,r6=t.u32(),r7=t.u32())
