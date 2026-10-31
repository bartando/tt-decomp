"""0x82157628: mapped/resource/flag gates, live fields after unlock and clear.

Check every byte and call. PPC emits dcbst for its 128-byte cache-line walk;
the emulator treats cache maintenance as architectural no-ops. Native hosts
use a release fence on their coherent mappings; GPU coherence is not tested.
"""
import struct
from liftcheck.spec import *

FUNCTION = 'grc_7628'
ADDRESS = 0x82157628
SOURCE = 'src/graphics/grc_vertex_buffer.cpp'
TRIALS = 800
EXTERNS = {'g_grcUseResourceLocks': 0x8260640C, 'rage::g_bTextureEndianDirty': 0x82606562}


def unlock(c):
    resource = c.r(3)
    buffer, data, count, stride = struct.unpack('>4I', c.read(resource + 0x20, 16))
    c.write(buffer + 0x1C, struct.pack('>I', data))
    c.write(buffer, struct.pack('>I', count))
    c.write(buffer + 0xD4, struct.pack('>I', stride))
    c.write(buffer + 0xDB, b'\x80')


CALLS = {0x82352CC8: model(unlock, args=('r3','r4','r5'))}


def inputs(t):
    rng = t.rng
    buffer = t.alloc(0x100, 'buffer and guards') + 16
    resource = t.alloc(0x40, 'resource')
    data = t.alloc(0x1000, 'mapped data')
    mapped = (0, 1, 2, 255)[t.index % 4]
    t.w8(buffer + 0xDB, mapped)
    t.w32(buffer + 0x10, resource if (t.index // 4) % 3 else 0)
    t.w32(buffer + 0x1C, data + rng.randrange(128))
    t.w32(buffer, rng.randrange(9))
    t.w32(buffer + 0xD4, rng.choice((0, 4, 16, 128)))
    t.w32(resource + 12, data | rng.randrange(4))
    t.w32(resource + 0x20, buffer)
    t.w32(resource + 0x24, data + rng.randrange(128))
    t.w32(resource + 0x28, rng.randrange(9))
    t.w32(resource + 0x2C, rng.choice((0, 4, 16, 128)))
    t.w8(0x8260640C, rng.choice((0, 1, 255)))
    t.w8(0x82606562, rng.choice((0, 1, 255)))
    t.args(r3=buffer)
