"""swfSCRIPTARRAY slot 10 (0x823FEB48): typed-key indexing and length lookup.

String keys (tags 0/1) only special-case "length"; even "0" delegates to the
script-object base. Other tags go through the original integer conversion.
Run both original conversion helpers, and model only the base lookup, checking
the complete key, destination, return value and its writes. Inputs cover empty
and full uint16 counts, signed index boundaries, all value tags, raw element
bits and overlapping result/element storage. No ignored bytes or float tolerance.
"""
import struct

from liftcheck.spec import *

FUNCTION = "rage::swfSCRIPTARRAY::GetMember"
ADDRESS = 0x823FEB48
SOURCE = "src/rage/swf.cpp"
TRIALS = 1000


def _base_lookup(ctx):
    ctx.write(ctx.r(5), ctx.rng.randbytes(8))
    ctx.ret(r3=ctx.rng.randrange(2))


CALLS = {
    0x823FA5C8: run(args=("r3",), deref={"r3": 8}),
    0x823FA768: run(args=("r3", "r4", "r5"), deref={"r3": 8}),
    0x823FBFC0: model(_base_lookup, args=("r3", "r4", "r5"), deref={"r4": 8}),
}


def inputs(t):
    rng = t.rng
    array = t.alloc(24, "array")
    count = rng.choice((0, 1, 2, 3, 8, 31, 255, 0x7FFF, 0x8000, 0xFFFF))
    # One extra element catches accidentally accepting index == count.
    elements = t.alloc((count + 1) * 8 + 8, "elementsAndGuard")
    t.w32(array + 16, elements)
    t.w16(array + 20, count)
    t.w16(array + 22, rng.randrange(0x10000))
    key = t.alloc(8, "key")
    tag = rng.choice((0, 1, 2, 3, 3, 3, 4, 5, 6, 7, 0xFFFFFFFF))
    t.w32(key + 4, tag)
    index = 0
    if tag in (0, 1):
        text = rng.choice((b"length", b"length", b"Length", b"lengthX", b"lengt", b"",
                           b"0", b"1", b"-1", b"custom", b"length\0tail",
                           b"long_property_" * 12))
        if tag == 1:
            t.w32(key, t.alloc(len(text) + 1, "keyText", fill=text + b"\0"))
        else:
            head = 0
            for chunk in reversed([text[i:i + 12] for i in range(0, len(text), 12)] or [b""]):
                node = t.alloc(16, "keyChunk", fill=chunk.ljust(12, b"\0"))
                t.w32(node + 12, head)
                head = node
            t.w32(key, head)
    elif tag == 2:
        # ToInteger reads the first payload byte, ignoring dirty padding.
        index = rng.choice((0, 1, 2, 127, 128, 255))
        t.w8(key, index)
    elif tag == 3:
        index = rng.choice((-0x80000000, -1, 0, 1, count - 1, count,
                            count + 1, 0x7FFFFFFF, rng.randrange(-2, count + 2)))
        t.w32(key, index)
    elif tag == 4:
        value = rng.choice((-float("inf"), float("inf"), float("nan"), -0.0,
                            -1.75, -0.75, 0.75, 1.75, float(count - 1),
                            float(count), float(count) + 0.75, 2147483648.0))
        t.w32(key, struct.unpack(">I", struct.pack(">f", value))[0])
        index = int(value) if -2147483648 <= value < 2147483648 else -0x80000000
    result = t.alloc(8, "result")
    if 0 <= index < count and tag not in (0, 1) and rng.randrange(3) == 0:
        # Original copies each word after the preceding store, including when
        # result points one word into the selected element.
        result = elements + index * 8 + rng.choice((0, 4))
    t.args(r3=array, r4=key, r5=result)
