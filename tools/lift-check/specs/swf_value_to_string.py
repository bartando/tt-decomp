"""util_A768_1: convert the SWF VM's 8-byte {payload, tag} value to text.

Covers every tag, invalid tags, null/direct strings, byte booleans with dirty
padding, signed ints, and arbitrary float32 bits (including NaNs, infinities,
signed zero, subnormals and the int32 saturation boundaries). Chunk chains have
random bytes/embedded NULs and deliberately small/negative maxLen values: the
original copies all 12 bytes per chunk regardless of maxLen.

Limits: finite acyclic, disjoint, aligned chunks with sufficient output storage;
numeric maxLen is nonnegative. _snprintf is modelled, not executed: this checks
its format, count, complete numeric argument and resulting writes, not the CRT
formatter itself. The model bridges the documented varargs ABI difference:
Xenon passes the double in 64-bit r6; SysV PPC32 passes it in f1. Both must equal
the independently prepared input payload. No ignored memory or float tolerance.
"""
import struct

from liftcheck.spec import *

FUNCTION = "util_A768_1"
ADDRESS = 0x823FA768
SOURCE = "src/rage/swf.cpp"
TRIALS = 1200

BUFFER_SIZE = 512
FLOAT_BITS = (
    0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x00800000,
    0x3F000000, 0xBF000000, 0x3F800000, 0xBF800000,
    0x4AFFFFFF, 0x4B000000, 0x4B000001,
    0x4EFFFFFF, 0x4F000000, 0x4F000001,
    0xCEFFFFFF, 0xCF000000, 0xCF000001,
    0x7F7FFFFF, 0xFF7FFFFF, 0x7F800000, 0xFF800000,
    0x7FC12345, 0xFFC12345, 0x7F812345, 0xFF812345,
)


def _snprintf(ctx):
    fmt = bytearray()
    while (byte := ctx.read(ctx.r(5) + len(fmt), 1)) != b"\0":
        fmt.extend(byte)
        assert len(fmt) <= 4
    fmt = fmt.decode()
    metadata = ctx.r(3) + BUFFER_SIZE
    tag = int.from_bytes(ctx.read(metadata, 4), "big")
    if tag == 3:
        assert fmt == "%d"
        payload = struct.pack(">I", ctx.r(6))
        assert payload == ctx.read(metadata + 4, 4), "integer vararg differs"
        number = struct.unpack(">i", payload)[0]
    else:
        assert tag == 4 and fmt in ("%0.f", "%f")
        payload = (struct.pack(">Q", ctx.rec.gpr64[3]) if ctx.side == "orig"
                   else struct.pack(">d", ctx.f(1)))
        expected = ctx.read(metadata + 4, 8)
        assert payload == expected, f"promoted double vararg {payload.hex()} != {expected.hex()}"
        number = struct.unpack(">d", payload)[0]
    text = (fmt % number).encode()
    count = ctx.r(4)
    # Microsoft's _snprintf does not terminate when the output fills the buffer.
    ctx.write(ctx.r(3), (text + b"\0")[:count])
    ctx.ret(r3=len(text) if len(text) <= count else -1)


CALLS = {
    "_snprintf": model(_snprintf, args=("r3", "r4", "r5")),
}


def inputs(t):
    rng = t.rng
    value = t.alloc(8, "value")
    buffer = t.alloc(BUFFER_SIZE + 16, "bufferAndExpectedArgument")
    tag = rng.choice((0, 1, 2, 3, 4, 5, 6, 7, 0x7FFFFFFF, 0x80000000, 0xFFFFFFFF))
    t.w32(value + 4, tag)
    max_len = rng.choice((0, 1, 2, 3, 7, 8, 11, 12, 13, 16, 32, 64, 256, BUFFER_SIZE))
    if tag == 0:
        head = 0
        for _ in range(rng.choice((0, 1, 2, 3, 8, 24))):
            chunk = t.alloc(16, "chunk")
            # Mix random full chunks and padded/embedded-NUL data.
            if rng.randrange(2):
                t.put(chunk, rng.randbytes(rng.randrange(13)).ljust(12, b"\0"))
            t.w32(chunk + 12, head)
            head = chunk
        t.w32(value, head)
        max_len = rng.choice((max_len, -1, -2147483648))
    elif tag == 1:
        text = rng.randbytes(rng.randrange(129)) + b"\0"
        t.w32(value, rng.choice((0, t.alloc(len(text), "directString", fill=text))))
    elif tag == 2:
        t.w8(value, rng.choice((0, 1, 2, 127, 128, 255)))
    elif tag == 3:
        payload = rng.choice((0, 1, 0xFFFFFFFF, 0x7FFFFFFF, 0x80000000, rng.getrandbits(32)))
        t.w32(value, payload)
        t.w32(buffer + BUFFER_SIZE, tag)
        t.w32(buffer + BUFFER_SIZE + 4, payload)
    elif tag == 4:
        bits = rng.choice((*FLOAT_BITS, rng.getrandbits(32)))
        t.w32(value, bits)
        number = struct.unpack(">f", struct.pack(">I", bits))[0]
        t.w32(buffer + BUFFER_SIZE, tag)
        if bits & 0x7F800000 == 0x7F800000:
            # lfs widens NaN payloads without quieting signalling NaNs.
            promoted = ((bits >> 31) << 63) | (0x7FF << 52) | ((bits & 0x7FFFFF) << 29)
            t.w64(buffer + BUFFER_SIZE + 4, promoted)
        else:
            t.put(buffer + BUFFER_SIZE + 4, struct.pack(">d", number))
    t.args(r3=value, r4=buffer, r5=max_len)
