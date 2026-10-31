"""0x82157578: lazy resource mapping, address masks, stack ABI and thread ID.

Map resource and thread APIs are modeled. Check the two stack arguments using
Xenon's 8-byte versus SysV's 4-byte slots. Model replaces the resource pointer;
the mapped result still comes from r3. All bytes/calls/returns compare exactly.
"""
import struct
from liftcheck.spec import *

FUNCTION = 'pg_7578_g'
ADDRESS = 0x82157578
SOURCE = 'src/graphics/grc_vertex_buffer.cpp'
TRIALS = 1000
EXTERNS = {'g_grcUseResourceLocks': 0x8260640C}


def lock(c):
    sp = c.m.gpr(1)
    offsets = (0x54, 0x5C) if c.side == 'orig' else (8, 12)
    flags, cache = (int.from_bytes(c.read(sp + off, 4), 'big') for off in offsets)
    assert flags == 0 and cache == 0x03000000, 'wrong lock stack arguments'
    resource = c.r(3)
    buffer, replacement, result = struct.unpack('>III', c.read(resource + 0x20, 12))
    c.write(buffer + 0x10, struct.pack('>I', replacement))
    c.write(buffer + 0xDB, b'\xFF')
    c.ret(r3=result)


CALLS = {0x823529E0: model(lock, args=('r3','r4','r5','r6','r7','r8','r9','r10')),
         0x82566B78: stub(ret=lambda c: c.rng.getrandbits(32), args=())}


def inputs(t):
    rng = t.rng
    buffer = t.alloc(0x100, 'buffer and guards') + 16
    resource = t.alloc(0x40, 'resource')
    data = t.alloc(64, 'data')
    replacement = t.alloc(0x20, 'replacement resource')
    mapped = (0, 1, 2, 255)[t.index % 4]
    present = t.index < 16 or (t.index // 4) % 3 != 0
    t.w8(buffer + 0xDB, mapped)
    t.w32(buffer + 0x10, resource if present else 0)
    if mapped and t.index >= 16 and t.index % 3 == 0:
        t.w32(buffer + 0x10, rng.getrandbits(32)) # skipped path must not touch it
    t.w32(resource + 4, rng.getrandbits(32))
    t.w32(resource + 12, data | rng.randrange(4))
    t.w32(resource + 16, rng.getrandbits(32))
    t.w32(resource + 0x20, buffer)
    t.w32(resource + 0x24, replacement)
    t.w32(resource + 0x28, rng.getrandbits(32))
    t.w8(0x8260640C, rng.choice((0, 1, 255)))
    t.args(r3=buffer)
