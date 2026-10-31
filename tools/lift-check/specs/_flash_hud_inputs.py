import struct
import zlib
from liftcheck.spec import *
state = {}


def _wait(ctx):
    assert ctx.r(4) == 0xFFFFFFFF
    # Even a failed wait causes the retail caller to mark the lock held.
    ctx.ret(r3=state['status'])


def _log(ctx):
    data = bytearray()
    while (c := ctx.read(ctx.r(3) + len(data), 1)) != b'\0':
        data.extend(c)
    ctx.rec.gpr[0] = zlib.crc32(data)
    ctx.write(state['hud'] + 0x5C, struct.pack('>I', state['replacement']))


CALLS = {
    'sysThread_WaitTimeout': model(_wait, args=('r3', 'r4')),
    'sysThread_ReleaseSemaphore': stub(ret=lambda c: state['status'], args=('r3', 'r4', 'r5')),
    'rage_debugLog': model(_log, args=('r3',)),
}
EXTERNS = {'rage_debugLog': 0x8240E6D0, '_pg_C3B8_g': 0x8242C3B8, '_pg_6DC0_g': 0x82566DC0}


def inputs(t):
    r = t.rng
    loop = t.alloc(0x240, 'gameLoop')
    manager = t.alloc(0x40, 'flashManager')
    t.w32(manager + 0x34, t.alloc(0x20, 'semaphore'))
    t.w32(loop + 0x22C, manager if t.index % 3 else 0)
    t.w32(0x825EAB30, loop)
    t.w8(0x826065EB, r.choice([0, 0, 1, 2, 0x80, 0xFF]))
    hud = t.alloc(0x80, 'hud')
    t.w32(hud + 0x5C, t.alloc(0xB0, 'group'))
    state.update(hud=hud, replacement=t.alloc(0xB0, 'replacementGroup'),
                 status=r.choice([0, 1, 0x102, 0xFFFFFFFF]))
    t.args(r3=hud)
