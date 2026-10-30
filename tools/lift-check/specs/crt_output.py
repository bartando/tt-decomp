"""Narrow CRT printf engine, compared against all 0xB84 original bytes.

Random combinations cover flags, star/numeric widths and precisions, signed and
unsigned 16/32/64-bit integers, pointer/octal/hex, narrow/wide/counted strings,
%n, literals/DBCS, float callbacks (including allocation failure), invalid stream
modes/arguments, debug streams, and output/conversion failures. Xenon varargs
start at every byte alignment. No ignored memory or tolerant comparisons.

Output helpers are modeled at their call boundary: emitted bytes, cursor,
remaining capacity and count are compared, as are helper calls and arguments.
Float conversion is a scripted callback, not a second implementation of printf;
its double input and formatting arguments are compared. Real numeric-to-decimal
float conversion, OS I/O and locale conversion internals are outside this spec.
"""
from liftcheck.spec import model, run, stub

FUNCTION = "crtOutput"
ADDRESS = 0x824348D0
SOURCE = "src/crt/printf.cpp"
TRIALS = 1200


def u32(ctx, p):
    return int.from_bytes(ctx.read(p, 4), "big")


def w32(ctx, p, value):
    ctx.write(p, (value & 0xFFFFFFFF).to_bytes(4, "big"))


def emit(ctx, stream, count, data):
    cursor, remaining = u32(ctx, stream), u32(ctx, stream + 4)
    n = u32(ctx, count)
    for ch in data:
        if remaining == 0:
            n = 0xFFFFFFFF
            break
        ctx.write(cursor, bytes([ch]))
        cursor += 1
        remaining -= 1
        n = (n + 1) & 0xFFFFFFFF
    w32(ctx, stream, cursor)
    w32(ctx, stream + 4, remaining)
    w32(ctx, count, n)


def write_char(ctx):
    emit(ctx, ctx.r(4), ctx.r(5), bytes([ctx.r(3) & 255]))


def write_block(ctx):
    size = ctx.r(4)
    if size & 0x80000000:
        size = 0
    assert size <= 4096
    emit(ctx, ctx.r(5), ctx.r(6), ctx.read(ctx.r(3), size))


def descriptor(ctx):
    ctx.ret(r3=u32(ctx, ctx.r(3) + 16))


def wide_char(ctx):
    ch = ctx.r(6)
    if ch >= 0xD800:
        ctx.ret(r3=42)
    else:
        data = chr(ch).encode("utf-8")
        assert len(data) <= ctx.r(5)
        ctx.write(ctx.r(4), data)
        w32(ctx, ctx.r(3), len(data))
        ctx.ret(r3=0)


def float_format(ctx):
    # Independent scripted result, driven by the double bits, rather than
    # host printf (which has different MSVC formatting/locale behavior).
    bits = int.from_bytes(ctx.read(ctx.r(3), 8), "big")
    text = (b"-" if bits >> 63 else b"") + b"12.3400"
    assert ctx.r(5) >= len(text) + 1
    ctx.write(ctx.r(4), text + b"\0")


def edit_float(ctx):
    p = ctx.r(3)
    data = bytearray()
    while ctx.read(p + len(data), 1) != b"\0":
        data.extend(ctx.read(p + len(data), 1))
    # Make postprocessing observable in the output as well as the call trace.
    data += b"!"
    ctx.write(p, data + b"\0")


def malloc(ctx):
    if ctx.rng.randrange(2):
        ctx.ret(r3=ctx.alloc(ctx.r(3)))
    else:
        ctx.ret(r3=0)


def debug_format(ctx):
    result = ctx.rng.choice([-1, 0, 14, 511])
    ctx.write(ctx.r(3), b"D" * 512 if result == -1 else b"debug callback\0")
    ctx.ret(r3=result)


def debug_string(ctx):
    # An unterminated 512-byte callback result must be truncated at byte 511.
    p = ctx.r(3)
    data = bytearray()
    while ctx.read(p + len(data), 1) != b"\0":
        data.extend(ctx.read(p + len(data), 1))
    assert data in (b"debug callback", b"D" * 511)


def ppc32_udivdi3(ctx):
    # Compiler runtime only: PPC32 lowers Xenon's native divdu to this helper.
    numerator = (ctx.r(3) << 32) | ctx.r(4)
    denominator = (ctx.r(5) << 32) | ctx.r(6)
    assert denominator
    quotient = numerator // denominator
    ctx.ret(r3=quotient >> 32)
    ctx.m.set_gpr(4, quotient & 0xFFFFFFFF)


HOST = {"__udivdi3": model(ppc32_udivdi3, transparent=True, preserves=("r4",))}


CALLS = {
    "crtWriteChar": model(write_char),
    "crtWriteBlock": model(write_block),
    "crtFileDescriptor": model(descriptor),
    "crtStandardStreams": run(),
    "crtErrno": stub(ret=0x825B13C4),
    "crtInvalidParameter": stub(ret="void"),
    "crtIsLeadByte": model(lambda c: c.ret(r3=int(c.r(3) == 0x81))),
    "crtWideCharToMultibyte": model(wide_char),
    "crtCountOutputEnabled": run(),
    "crtMalloc": model(malloc),
    "crtFree": stub(ret="void"),
    "float.format": model(float_format, args=("r3", "r4", "r5", "r6", "r7", "r8", "r9"), deref={"r3": 8}),
    "float.crop": model(edit_float, args=("r3", "r4")),
    "float.decimal": model(edit_float, args=("r3", "r4")),
    "crtVsnprintf": model(debug_format),
    "crtDebugString": model(debug_string),
}


def inputs(t):
    rng = t.rng
    output = t.alloc(4096, "outputAndGuards")
    stream = t.alloc(32, "file")
    t.w32(stream, output + 16)
    t.w32(stream + 4, rng.choice([0, 1, 5, 12, 32, 2048, 2048, 2048]))
    t.w32(stream + 8, output + 16)
    t.w32(stream + 12, 0x42)
    t.w32(stream + 16, rng.choice([-2, -1, 0, 31, 32, 63, 95]))
    slots = t.alloc(256, "xenonVarargs")
    start = slots + rng.randrange(8)
    arg = (start + 7) & ~7

    def word(value):
        nonlocal arg
        t.w32(arg + 4, value)
        arg += 8

    def wide(value):
        nonlocal arg
        t.w64(arg, value)
        arg += 8

    text = t.alloc(64, "text", fill=b"hello\0ignored")
    utf16 = t.alloc(64, "utf16", fill="zero")
    for i, ch in enumerate(rng.choice([[65, 66, 67], [0xE9, 32, 0x3A9], [65, 0xD800, 66], []])):
        t.w16(utf16 + i * 2, ch)
    counted = t.alloc(8, "countedString")
    t.w16(counted, rng.choice([0, 1, 5, 8]))
    t.w32(counted + 4, rng.choice([0, text]))
    count_dst = t.alloc(16, "percentNAndGuards")
    kind = rng.randrange(18)
    fmt = b"head:"
    if kind < 5:
        conversion = rng.choice([b"d", b"i", b"u", b"o", b"x", b"X", b"p"])
        modifier = rng.choice([b"", b"h", b"l", b"ll", b"I64", b"I32", b"I"])
        flags = rng.choice([b"", b"-", b"+", b" ", b"#", b"0", b"+#0", b"-0", b" +"])
        width = rng.choice([b"", b"1", b"9", b"24", b"*"])
        precision = rng.choice([b"", b".0", b".1", b".8", b".31", b".513", b".*"])
        fmt += b"%" + flags + width + precision + modifier + conversion
        if width == b"*": word(rng.choice([-24, -1, 0, 1, 16]))
        if precision == b".*": word(rng.choice([-20, -1, 0, 1, 8, 20, 513]))
        value = rng.choice([0, 1, 0x7FFF, 0x8000, 0xFFFF, 0x7FFFFFFF, 0x80000000,
                            0xFFFFFFFF, 0x8000000000000000, 0xFFFFFFFFFFFFFFFF, rng.getrandbits(64)])
        if modifier in (b"ll", b"I64"): wide(value)
        else: word(value)
    elif kind == 5:
        fmt += rng.choice([b"%s", b"%20.3s", b"%-9s", b"%.0s"])
        word(rng.choice([0, text]))
    elif kind == 6:
        fmt += rng.choice([b"%S", b"%ls", b"%ws", b"%12.2S", b"%-8ls"])
        word(rng.choice([0, utf16]))
    elif kind == 7:
        fmt += rng.choice([b"%c", b"%C", b"%hc", b"%lc", b"%wc", b"%hC"])
        word(rng.choice([0, 65, 255, 0x3A9, 0xD800]))
    elif kind == 8:
        is_wide = rng.choice([False, True])
        fmt += b"%wZ" if is_wide else b"%Z"
        if is_wide:
            t.w16(counted, rng.choice([0, 2, 4, 6]))
            t.w32(counted + 4, utf16)
        word(rng.choice([0, counted]))
    elif kind == 9:
        fmt += rng.choice([b"%n", b"%hn", b"%ln", b"%I64n"])
        word(count_dst + 4)
    elif kind in (10, 11):
        fmt += (b"%" + rng.choice([b"", b"#", b"+", b"0", b"-", b" "])
                + rng.choice([b"", b"24"])
                + rng.choice([b"", b".0", b".2", b".164", b".600"])
                + rng.choice([b"a", b"A", b"e", b"E", b"f", b"g", b"G"]))
        wide(rng.getrandbits(64))
    elif kind == 12:
        fmt = rng.choice([b"", b"literal\n", b"%% done", b"trailing%", b"%q|%Id|%I!", b"\x81A!", b"\x81"])
        word(123)
    elif kind == 13:
        fmt = b"%d/%#x/%-8.3s/%hn"
        word(rng.getrandbits(32)); word(rng.getrandbits(32)); word(text); word(count_dst + 4)
    elif kind in (14, 15):
        # Descriptor lookup spans IO blocks, plus -1/-2's bad-entry path.
        t.w32(stream + 12, 2)
        blocks = [t.alloc(44 * 32, f"ioBlock{i}") for i in range(3)]
        for i, block in enumerate(blocks):
            t.w32(0x82732F40 + 4 * i, block)
            for j in range(32):
                t.w8(block + 44 * j + 40, rng.choice([0, 0, 1, 2, 0x80]))
        t.w8(0x825B13C4 + 40, rng.choice([0, 0, 1, 2]))
        fmt = b"mode check"
    elif kind == 16:
        fmt = b"debug %d"
        stream = 0x825B0C38 + rng.choice([32, 64])
        t.w32(stream + 12, 0x42)
        word(rng.getrandbits(32))
    else:
        if rng.choice([False, True]): stream = 0
        else: fmt = None

    # _get_printf_count_output compares a cookie with its startup copy.
    cookie = rng.getrandbits(32)
    t.w32(0x825E70D4, cookie)
    t.w32(0x825B1D50, cookie if rng.choice([False, True]) else cookie ^ 1)
    t.w32(0x825B14F0 + 24, t.fake_fn("float.format"))
    t.w32(0x825B14F0 + 32, t.fake_fn("float.crop"))
    t.w32(0x825B14F0 + 36, t.fake_fn("float.decimal"))
    address = 0 if fmt is None else t.alloc(len(fmt) + 4, "format", fill=fmt + b"\0\0\0\0")
    t.args(r3=stream, r4=address, r5=rng.getrandbits(32), r6=start)
