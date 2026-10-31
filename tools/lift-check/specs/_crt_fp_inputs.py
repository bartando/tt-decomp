import math
import struct

def bits(value):
    return struct.unpack(">d", struct.pack(">Q", value & 0xFFFFFFFFFFFFFFFF))[0]

VALUES = [0, 0x8000000000000000, 1, 0x8000000000000001,
          0x000FFFFFFFFFFFFF, 0x0010000000000000, 0x7FEFFFFFFFFFFFFF,
          0xFFEFFFFFFFFFFFFF, 0x7FF0000000000000, 0xFFF0000000000000,
          0x7FF0000000000001, 0xFFF0000000000001,
          0x7FF7FFFFFFFFFFFF, 0xFFF7FFFFFFFFFFFF,
          0x7FF8000000000000, 0xFFF8000000000000,
          0x7FF8000000000042, 0xFFF8000000000042]

def value(t):
    return bits(VALUES[t.index] if t.index < len(VALUES) else t.rng.getrandbits(64))

def inputs(t):
    t.args(f1=value(t))

def round_inputs(t):
    ties = [sign * x for sign in (1, -1)
            for x in (0., .25, .5, .75, 1.5, 2.5, 3.5, 2**51-.5, 2**52-0.5, 2**52)]
    if t.index < len(ties) * 3:
        x = ties[t.index // 3]
        x = [math.nextafter(x, -math.inf), x, math.nextafter(x, math.inf)][t.index % 3]
    elif t.index < len(ties) * 3 + len(VALUES):
        x = bits(VALUES[t.index - len(ties) * 3])
    else:
        x = value(t)
    t.args(f1=x)
