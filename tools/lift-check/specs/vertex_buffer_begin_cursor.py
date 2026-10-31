"""0x821554B0: map only when needed, then reload the mapped cursor."""
import struct
from liftcheck.spec import *

FUNCTION = 'pg_54B0_g'
ADDRESS = 0x821554B0
SOURCE = 'src/graphics/grc_vertex_buffer.cpp'
TRIALS = 600


def mapping(c):
    buffer = c.r(3)
    c.write(buffer + 0x1C, struct.pack('>I', c.rng.getrandbits(32)))
    c.write(buffer + 0xDB, b'\x01')
    c.ret(r3=1)


CALLS = {0x82157578: model(mapping, args=('r3',))}


def inputs(t):
    buffer = t.alloc(0x100, 'buffer and guards') + 16
    t.w8(buffer + 0xDB, (0, 1, 2, 255)[t.index % 4])
    t.args(r3=buffer, r4=t.rng.getrandbits(32))
