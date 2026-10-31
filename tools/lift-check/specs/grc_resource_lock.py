"""0x823529E0: fence wait, owner-thread packets, atomic ranges and dirty spans.

Run the original reservation loop. The PPC32 checker compiler lowers portable
64-bit atomics to libatomic calls; transparent models below implement that ABI
(the synthetic addresses are checker-runtime symbols, not original routines).
No concurrent writer is injected: compare the uncontended atomic result, not
interrupt scheduling. Kernel process/thread, fence and command-refill boundaries
are modeled and can replace resource flags, device owner and command pointers.
"""
from liftcheck.spec import *

FUNCTION = 'grcResource_Lock'
ADDRESS = 0x823529E0
SOURCE = 'src/graphics/grc_gpu_resources.cpp'
TRIALS = 500
EXTERNS = {'__atomic_load_8': 0x81700000, '__atomic_compare_exchange_8': 0x81700010}


def u(c, a, n=4): return int.from_bytes(c.read(a, n), 'big')
def w(c, a, value, n=4): c.write(a, (value & ((1 << (n*8))-1)).to_bytes(n, 'big'))


def atomic_load(c):
    value = u(c, c.r(3), 8)
    c.ret(r3=value >> 32)
    c.m.set_gpr(4, value & 0xFFFFFFFF)
    c.rec.ret['r4'] = value & 0xFFFFFFFF


def atomic_cas(c):
    address, expected = c.r(3), c.r(4)
    value = u(c, address, 8)
    success = value == u(c, expected, 8)
    if success:
        w(c, address, (c.r(5) << 32) | c.r(6), 8)
    else:
        w(c, expected, value, 8)
    c.ret(r3=int(success))


def process_type(c): c.ret(r3=c.rng.choice((0, 1, 2, 2, 3)))
def thread(c): c.ret(r3=c.rng.choice((0x111, 0x222)))


def wait(c):
    device = c.r(3)
    res = u(c, device + 0x2D00)
    w(c, res, u(c, device + 0x2D04))
    w(c, device + 0x2888, u(c, device + 0x2D0C))
    w(c, c.r(4), 0)


def refill(c):
    device = c.r(3)
    result = u(c, device + 0x2D10)
    w(c, device, result + 4)  # decoy; use the returned cursor
    w(c, u(c, device + 0x2D00), u(c, device + 0x2D08))
    c.ret(r3=result)


CALLS = {
    0x82585E9C: model(process_type, args=()),
    0x82566B78: model(thread, args=()),
    0x8235AA78: model(wait, args=('r3', 'r4'), deref={'r4': 4}),
    0x8235A980: model(refill, args=('r3',)),
    '__atomic_load_8': model(atomic_load, transparent=True, args=()),
    '__atomic_compare_exchange_8': model(atomic_cas, transparent=True, args=()),
}


def inputs(t):
    rng = t.rng
    t.map(0x81700000, 0x1000, 'checker libatomic runtime', fill='zero')
    resource = t.alloc(0x30, 'resource and guards')
    noise = rng.getrandbits(32)
    state_flags = (0, 0x40000000, 0x00800000, 0x40780000)[t.index % 4]
    t.w32(resource, (noise & ~0x40F80000) | state_flags)
    for off in (8, 12):
        t.w32(resource + off, rng.choice((0xFFFF0000, 0, 0x0001FFFF, rng.getrandbits(32))))
    for slot, name in ((0x82000730, 'title'), (0x82000734, 'xam')):
        cell = t.alloc(4, name + ' import cell')
        device = t.alloc(0x2D40, name + ' device')
        commands = t.alloc(128, name + ' commands') + 16
        refill_commands = t.alloc(128, name + ' refill commands') + 16
        t.w32(slot, cell)
        t.w32(cell, device)
        t.w32(device, commands)
        t.w32(device + 8, commands + rng.choice((-4, 0, 4, 64)))
        t.w32(device + 0x2888, rng.choice((0x111, 0x222)))
        t.w32(device + 0x289C, rng.choice((0, 0, 1, 0xFFFFFFFF, rng.getrandbits(32))))
        t.w64(device + 0x2C98, rng.choice((0x00000000FFFFFFFF, 0, 0xFFFFFFFF00000000,
                                        rng.getrandbits(64))))
        t.w32(device + 0x2D00, resource)
        t.w32(device + 0x2D04, rng.getrandbits(32))
        t.w32(device + 0x2D08, rng.getrandbits(32))
        t.w32(device + 0x2D0C, rng.choice((0x111, 0x222)))
        t.w32(device + 0x2D10, refill_commands)
    data = rng.choice((0, 0x7FFFFFFF, 0x80000000, 0xA0001234, 0xC0000800,
                       0xE0000000, 0xFFFFFFFF, rng.getrandbits(32)))
    size = rng.choice((0, 1, 127, 128, 129, 4095, 4096, 4097, rng.getrandbits(32)))
    base = (data + rng.choice((-4096, -127, -1, 0, 128))) & 0xFFFFFFFF
    auxiliary_base = rng.choice((0, base ^ 0x1234, data))
    flags = (rng.getrandbits(32) & ~0x1013) | (0, 1, 2, 0x10, 0x12, 0x1000,
                                           0x1001, 0x1010, 0x1012)[t.index % 9]
    cache = rng.getrandbits(32)
    # Original Xenon uses eight-byte argument slots; SysV PPC32 uses four.
    for off in (0x54, 8): t.w32(t.sp + off, flags)
    for off in (0x5C, 12): t.w32(t.sp + off, cache)
    t.args(r3=resource, r4=rng.choice((0, 1, rng.getrandbits(32))), r5=rng.getrandbits(32),
           r6=rng.choice((0, 1, 255)), r7=base, r8=auxiliary_base, r9=data, r10=size)
