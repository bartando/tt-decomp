"""All left tags, coercion call boundaries, and asymmetric object equality.

Coercions are models: text copies the supplied right string to its output;
boolean/integer/float return the right payload, including dirty boolean upper
bits. This checks dispatch and comparisons independently of coercion internals.
"""
import struct
from liftcheck.spec import *

FUNCTION = "swfValuesEqual"
ADDRESS = 0x823FA928
SOURCE = "src/rage/swf_value_helpers.cpp"
TRIALS = 800


def _string(c):
    address = int.from_bytes(c.read(c.r(3), 4), "big")
    text = bytearray()
    while True:
        byte = c.read(address + len(text), 1)
        text += byte
        if byte == b"\0":
            break
    c.write(c.r(4), text)
    c.ret(r3=c.r(4))


def _word(c):
    c.ret(r3=int.from_bytes(c.read(c.r(3), 4), "big"))


def _float(c):
    c.ret(f1=struct.unpack(">f", c.read(c.r(3), 4))[0])


CALLS = {
    0x823FA768: model(_string, args=("r3", "r4", "r5")),
    0x823FA420: model(_word, args=("r3",)),
    0x823FA5C8: model(_word, args=("r3",)),
    0x823FA688: model(_float, args=("r3",)),
}


def inputs(t):
    rng = t.rng
    a = t.alloc(8, "left")
    b = t.alloc(8, "right")
    tag = t.index % 10
    t.w32(a + 4, tag)
    t.w32(b + 4, rng.choice((0, 1, 2, 3, 4, 5, 6, 7, 0xffffffff)))
    if tag <= 1:
        text = rng.choice((b"", b"same", b"twelve_bytes!", b"long_" * 180, b"\xff\x80ABC"))
        other = text if rng.randrange(2) else text + b"different"
        t.w32(b, t.alloc(len(other) + 1, "rightText", fill=other + b"\0"))
        if tag == 1:
            head = t.alloc(len(text) + 1, "leftText", fill=text + b"\0")
        else:
            head = 0
            for chunk in reversed([text[i:i + 12] for i in range(0, len(text), 12)] or [b""]):
                node = t.alloc(16, "leftChunk", fill=chunk.ljust(12, b"\0"))
                t.w32(node + 12, head)
                head = node
        t.w32(a, head)
    elif tag == 2:
        byte = rng.randrange(256)
        t.w8(a, byte)
        t.w32(b, (rng.getrandbits(24) << 8) | (byte if rng.randrange(2) else rng.randrange(256)))
    elif tag == 4:
        bits = rng.choice((0, 0x80000000, 0x3f800000, 0x7f800000,
                           0xff800000, 0x7fc00000, 1, 0x7f7fffff))
        t.w32(a, bits)
        t.w32(b, bits if rng.randrange(2) else rng.getrandbits(32))
    else:
        word = rng.choice((0, 1, 0xffffffff, rng.getrandbits(32)))
        t.w32(a, word)
        t.w32(b, word if rng.randrange(2) else rng.getrandbits(32))
    t.args(r3=a, r4=b)
