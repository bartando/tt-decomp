"""Every SWF tag, dirty bool padding, signed integer rounding and float bits.

atof is a boundary: compare text/pointer and double-to-single return rounding.
Include finite doubles beyond float range, subnormals, signed zero, NaN/Inf.
Tag 0 is direct text too; no chunk flattening. No ignored memory or tolerance.
FPSCR and the CRT's parsing algorithm are outside this spec.
"""
from liftcheck.spec import *
from specs.swf_value_to_integer import FLOAT_BITS, TAGS

FUNCTION = "swfValueToFloat"
ADDRESS = 0x823FA688
SOURCE = "src/rage/swf.cpp"
TRIALS = 1200


def parsed(c):
    c.ret(f1=c.rng.choice((0., -0., 1.0000000596046448, -2147483649.,
                         1e100, -1e100, 1e-40, -1e-40,
                         float('inf'), float('-inf'), float('nan'),
                         c.rng.uniform(-1e8, 1e8))))


CALLS = {0x82432B80: model(parsed, args=("r3",))}


def inputs(t):
    r = t.rng
    value = t.alloc(8, "value")
    tag = 4 if t.index % 2 == 0 else TAGS[(t.index // 2) % len(TAGS)]
    t.w32(value + 4, tag)
    if tag in (0, 1):
        text = r.choice((b"", b"0", b"-17.2", b" +42tail", b"1e100", b"nan", b"nonsense"))
        chunk = t.alloc(16, "textOrFirstChunk", fill=text + b"\0")
        t.w32(chunk + 12, t.alloc(16, "unusedNextChunk", fill=b"98765\0"))
        t.w32(value, chunk)
    elif tag == 2:
        t.w32(value, t.u32())
        t.w8(value, r.choice((0, 1, 2, 127, 128, 255)))
    elif tag == 3:
        t.w32(value, r.choice((0, 1, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000,
                              0x01000001, 0xFEFFFFFF, t.u32())))
    elif tag == 4:
        t.w32(value, FLOAT_BITS[(t.index // 2) % len(FLOAT_BITS)]
              if t.index % 2 == 0 else t.u32())
    else:
        t.w32(value, t.u32() | 1)
    t.args(r3=value)
