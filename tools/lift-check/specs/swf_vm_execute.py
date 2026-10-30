"""ActionScript bytecode dispatch at util_F7E8 (0x823FF7E8).

Coverage: all 256 opcode bytes (unsupported opcodes log and skip), all Push
encodings, local/external registers, reset/preserved stacks, bounded/unbounded
execution, forward/backward branches, arithmetic/conversion/comparison paths,
member/call dispatch (including modelled VM re-entry), constant pools and both
function-definition formats. The default 4000-trial run uses seed 1.

Limits: valid terminating streams, enough stack/register/pool capacity, string
buffers <=127 bytes, nonnegative substring lengths, <=4 function arguments and
<=4 legacy parameters; RandomNumber divisor nonzero; no signed division overflow.
The retail float32 Push leaves its cursor on the payload: float records end the
stream there with either a zero low payload byte or GetTimer followed by zero.
The latter makes accidentally fixing the cursor bug fail the call comparison.
All other Push types are mixed in the same record.
Unterminated/overflowing streams and original trap paths are outside this check.
External callees remain boundaries: numeric conversions execute original code;
CRT text parsing/formatting, string allocation/interning, clock, object methods
and function storage are models. Models check arguments/pointees and make
observable writes; they do not validate callee internals. Function-definition scratch has unspecified untouched
bytes, so its copy model checks only initialized fields. Boolean payload bytes
1..3 are uninitialized padding in the original; only those bytes of known boolean
outputs are ignored. No float tolerance. Return type is void (callers discard r3).
"""
import struct
from liftcheck.spec import *

FUNCTION = "util_F7E8"
ADDRESS = 0x823FF7E8
SOURCE = "src/rage/swf_vm.cpp"
TRIALS = 4000

STACK = 0x82715C98
DEPTH = 0x82604D1C
CONSTANTS = 0x82604D20


def u32(ctx, address):
    return int.from_bytes(ctx.read(address, 4), "big")


def cstr(ctx, address):
    out = bytearray()
    while (c := ctx.read(address + len(out), 1)) != b"\0":
        out += c
        assert len(out) < 1024
    return bytes(out)


def _snprintf(ctx):
    fmt = cstr(ctx, ctx.r(5)).decode()
    if fmt == "%d":
        value = struct.unpack(">i", struct.pack(">I", ctx.r(6)))[0]
    else:
        assert fmt in ("%f", "%0.f")
        value = struct.unpack(">d", struct.pack(">Q", ctx.rec.gpr64[3]))[0]
    data = (fmt % value).encode()
    ctx.write(ctx.r(3), (data + b"\0")[:ctx.r(4)])
    ctx.ret(r3=len(data))


def _strchr(ctx):
    data = cstr(ctx, ctx.r(3)) + b"\0"
    at = data.find(bytes([ctx.r(4) & 255]))
    ctx.ret(r3=ctx.r(3) + at if at >= 0 else 0)


def _atoi(ctx):
    import re
    match = re.match(rb"\s*([+-]?[0-9]+)", cstr(ctx, ctx.r(3)))
    ctx.ret(r3=int(match[1]) if match else 0)


def _atof(ctx):
    try:
        value = float(cstr(ctx, ctx.r(3)))
    except ValueError:
        value = 0.0
    ctx.ret(f1=value)


def _copy_string(ctx):
    data = cstr(ctx, ctx.r(3))
    head = 0
    for start in reversed(range(0, max(1, len(data)), 12)):
        node = ctx.alloc(16)
        ctx.write(node, data[start:start + 12].ljust(12, b"\0") + struct.pack(">I", head))
        head = node
    ctx.ret(r3=head)


def _intern(ctx):
    data = cstr(ctx, ctx.r(3))
    result = ctx.alloc(len(data) + 1)
    ctx.write(result, data + b"\0")
    ctx.ret(r3=result)


def _reenter(ctx):
    # A script method may execute another action list on the shared VM stack.
    depth = u32(ctx, DEPTH)
    for _ in range(ctx.rng.randrange(3)):
        ctx.write(STACK + 8 * depth, struct.pack(">II", ctx.rng.randrange(100), 3))
        depth += 1
    ctx.write(DEPTH, struct.pack(">I", depth))


def _get(ctx):
    key = ctx.read(ctx.r(4), 8)
    assert len(key) == 8
    result = ctx.r(5)
    assert ctx.read(result, 8) == struct.pack(">II", 0, 7)
    success = ctx.rng.choice((0, 1, 0x100, 0x101, 255))
    if success & 255:
        ctx.write(result, struct.pack(">II", ctx.rng.randrange(100), 3))
    ctx.write(ctx.r(3) + 0x40, key)
    _reenter(ctx)
    ctx.ret(r3=success)


def _set(ctx):
    ctx.write(ctx.r(3) + 0x30, ctx.read(ctx.r(5), 8))
    ctx.write(ctx.r(3) + 0x40, ctx.read(ctx.r(4), 8))
    _reenter(ctx)
    ctx.ret(r3=ctx.rng.getrandbits(32))


def _invoke(ctx):
    count = ctx.r(5)
    assert count <= 8
    # Make all arguments observable, not just the first pair's typed deref.
    ctx.write(ctx.r(3) + 0x40, ctx.read(ctx.r(6), count * 8))
    import zlib
    ctx.write(ctx.r(3) + 0x3C, struct.pack(">I", zlib.crc32(cstr(ctx, ctx.r(4)))))
    # The output starts as the undefined pair.
    assert ctx.read(ctx.r(7), 8) == struct.pack(">II", 0, 7)
    ctx.write(ctx.r(7), struct.pack(">II", ctx.rng.randrange(100), 3))
    _reenter(ctx)


def _delete(ctx):
    assert ctx.read(ctx.r(5), 8) == struct.pack(">II", 0, 7)
    ctx.write(ctx.r(5), struct.pack(">II", 17, 3))


def _strncpy(ctx):
    n = ctx.r(5)
    data = cstr(ctx, ctx.r(4))[:n]
    ctx.write(ctx.r(3), data.ljust(n, b"\0"))
    ctx.ret(r3=ctx.r(3))


def _strncmp(ctx):
    a = cstr(ctx, ctx.r(3))[:ctx.r(5)]
    b = cstr(ctx, ctx.r(4))[:ctx.r(5)]
    ctx.ret(r3=(a > b) - (a < b))


def _copy_function(ctx):
    # Normalize only the source's initialized fields into persistent storage.
    src, dst = ctx.r(4), ctx.r(3)
    count = u32(ctx, src + 0x84)
    assert count <= 8
    assert u32(ctx, src) == 0x82075314
    assert ctx.read(src + 0x898, 1) == b"\0"
    for off, size in ((4, 128), (0x84, 4), (0x88, count * 128),
                      (0x488, 8), (0x890, 8), (0x898, 1)):
        ctx.write(dst + off, ctx.read(src + off, size))
    ctx.ret(r3=dst)


CALLS = {
    0x82569394: run(transparent=True),  # MSVC dynamic-stack page probe
    0x82434520: MODELS["memcpy"], 0x82434100: MODELS["memcpy"],
    0x820C0B40: model(_snprintf, args=("r3", "r4", "r5", "r6")),
    0x824321B0: model(_strchr, args=("r3", "r4")),
    0x82432120: model(_atoi, args=("r3",)),
    0x82432B80: model(_atof, args=("r3",)),
    0x823FA420: run(), 0x823FA4C8: run(), 0x823FA5C8: run(),
    0x823FA688: run(), 0x823FA768: run(), 0x823FA928: run(),
    0x823FABC0: model(_copy_string, args=("r3",)),
    0x823F9FB0: model(_intern, args=("r3",)),
    0x8240E6D0: stub(ret="void", args=("r3",), auto_out=False),
    0x82566F98: stub(ret=lambda ctx: ctx.rng.getrandbits(32), args=()),
    0x82430120: model(_strncpy, args=("r3", "r4", "r5")),
    0x824320D0: model(_strncmp, args=("r3", "r4", "r5")),
    0x824032F0: alloc(size=0x1CA8, args=("r3", "r4")),
    0x82402FC0: model(_copy_function, args=("r3",)),
    0x82403090: model(_invoke, args=("r3", "r4", "r5", "r6", "r7", "r8")),
    "target.vfn_10": model(_get, args=("r3", "r4", "r5"), deref={"r4": 8}),
    "target.vfn_11": model(_set, args=("r3", "r4", "r5"), deref={"r4": 8, "r5": 8}),
    "target.vfn_12": model(_delete, args=("r3", "r4", "r5")),
    "target.vfn_13": model(_invoke, args=("r3", "r4", "r5", "r6", "r7")),
    "command": stub(ret="void", args=("r3", "r4"), deref={"r4": 8}, auto_out=False),
}
for slot in range(1, 6):
    CALLS[f"target.vfn_{slot}"] = stub(ret="void", args=("r3", "r4", "r5") if slot == 1
                                     else ("r3", "r4") if slot == 2 else ("r3",), auto_out=False)
# Objects allocated inline carry retail vtables, so use the same models there.
for address in (0x823FC8A8, 0x823FEC38):
    CALLS[address] = CALLS["target.vfn_11"]
for address in (0x823FEA28, 0x823FE500):
    CALLS[address] = CALLS["target.vfn_13"]


def action(op, payload=b""):
    return bytes([op]) + (struct.pack("<H", len(payload)) + payload if op & 128 else b"")


def inputs(t):
    rng = t.rng
    target = t.alloc(128, "target")
    t.w32(target, t.vtable("target"))
    context = t.alloc(128, "context")
    registers = t.alloc(2048, "registers")
    texts = (b"", b"abc", b"length", b"Array", b"HUD", b"FSCommand:test", b"xyz")
    strings = [t.alloc(len(s) + 1, "text", fill=s + b"\0") for s in texts]
    values = [(rng.getrandbits(32), 3), (rng.randrange(100), 3),
              (struct.unpack(">I", struct.pack(">f", rng.uniform(-100, 100)))[0], 4),
              (strings[rng.randrange(len(strings))], 1), (target, 5), (0, 7),
              (rng.choice((0, 1, 127, 255)) << 24, 2)]
    for i in range(256):
        v = rng.choice(values)
        t.w32(registers + 8 * i, v[0]); t.w32(registers + 8 * i + 4, v[1])
    for i in range(32):
        v = rng.choice(values)
        t.w32(STACK + i * 8, v[0]); t.w32(STACK + i * 8 + 4, v[1])
    for i in range(256):
        t.w32(CONSTANTS + i * 4, rng.choice(strings))
    t.w32(0x826066D8, rng.randrange(9))
    t.w32(0x826066D0, rng.randrange(4))
    t.w32(0x826066D4, rng.choice((0, t.fake_fn("command"))))
    t.w32(0x825E5A98, rng.getrandbits(32))
    # Every inline allocation has a valid free node, with a known virtual table.
    for address in (0x82604C60, 0x82604C58):
        pool = t.alloc(16, "objectPool")
        obj = t.alloc(128, "freeObject")
        t.w32(obj, 0)
        t.w32(pool + 12, obj); t.w16(pool + 6, rng.randrange(1, 65536))
        t.w32(address, pool)
    t.w16(0x82715F98 + 4, rng.randrange(1, 5))
    t.w32(0x82715F98, t.alloc(0x1CA8 * 4, "functionPool"))

    op = rng.randrange(256)
    initial = rng.choice((0, 1, 2, 3, 8))
    keep = rng.randrange(2)
    if op in (0x4C, 0x4D, 0x87): initial, keep = 3, 1
    program = b""
    boolean_slot = None
    if op == 0x96:
        payload = bytearray()
        # The original float32 Push forgets to advance over its payload.
        # Put it last; its data starts with End or GetTimer, then End.
        kinds = [0, 2, 3, 4, 5, 6, 7, 8, 9]; rng.shuffle(kinds); kinds.append(1)
        for kind in kinds:
            payload.append(kind)
            if kind == 0: payload += rng.choice(texts) + b"\0"
            elif kind in (1, 7):
                bits = rng.choice((0, 0x80000000, 0x7F800000, 0xFF800000,
                                   0x7F800100, 0x7FC12300, 0xFFC12300,
                                   rng.getrandbits(32))) if kind == 1 else rng.getrandbits(32)
                if kind == 1:
                    bits = (bits & 0xFFFF0000) | (0x34 if bits & 0x10000 else 0)
                payload += struct.pack("<I", bits)
            elif kind in (4, 5, 8): payload += bytes([rng.randrange(256)])
            elif kind == 6:
                bits = rng.choice((0, 0x8000000000000000, 0x3FF0000000000000,
                                   0x7FF0000000000000, 0x7FF8123456789ABC,
                                   rng.getrandbits(64)))
                payload += struct.pack("<II", bits >> 32, bits & 0xFFFFFFFF)
            elif kind == 9: payload += struct.pack("<H", rng.randrange(256))
        program = action(op, payload)
        base = initial if keep else 0
        boolean_slot = base + kinds.index(5)
    elif op == 0x81: program = action(op, struct.pack("<H", rng.randrange(65536)))
    elif op == 0x83: program = action(op, rng.choice((b"FSCommand:test\0arg\0", b"https:abc\0x\0")))
    elif op == 0x87: program = action(op, bytes([rng.randrange(256)]))
    elif op == 0x88:
        names = [rng.choice(texts) + b"\0" for _ in range(rng.randrange(9))]
        program = action(op, struct.pack("<H", len(names)) + b"".join(names))
    elif op in (0x99, 0x9D):
        # A branch skips a visible GetTimer; false If executes it.
        program = action(op, struct.pack("<h", 1)) + action(0x34)
    elif op in (0x8E, 0x9B):
        names = [b"param" + bytes([65 + i]) + b"\0" for i in range(rng.randrange(5))]
        name = rng.choice((b"", b"named")) + b"\0"
        body = b"\x34\0"
        if op == 0x8E:
            payload = name + struct.pack("<H", len(names)) + bytes([rng.randrange(256), 0, 0])
            payload += b"".join(bytes([i + 1]) + s for i, s in enumerate(names))
            payload += struct.pack("<H", len(body)) + body
        else:
            payload = name + struct.pack(">H", len(names)) + b"".join(names) + struct.pack(">H", len(body)) + body
        program = action(op, payload)
    else:
        program = action(op, b"ignored" if op & 128 else b"")

    # Constrain operands only where the original expects pointers/counts.
    def slots(items):
        nonlocal initial, keep
        initial, keep = len(items), 1
        for i, (payload, tag) in enumerate(items):
            t.w32(STACK + 8 * i, payload); t.w32(STACK + 8 * i + 4, tag)

    if op in (0x30,): slots([(rng.randrange(1, 1000), 3)])
    if op in (0x15, 0x35): slots([(strings[1], 1), (rng.randrange(-1, 5), 3), (rng.randrange(6), 3)])
    if op in (0x3D, 0x40, 0x52):
        count = rng.randrange(5)
        items = [rng.choice(values) for _ in range(count)] + [(count, 3)]
        if op == 0x52: items += [(target, rng.choice((3, 5)))]
        items += [(rng.choice((strings[3], strings[4])), 1)]
        slots(items)
    if op == 0x43:
        count = rng.randrange(5)
        slots(sum(([(rng.choice(strings), 1), rng.choice(values[:2])] for _ in range(count)), []) + [(count, 3)])
    if op == 0x42:
        count = rng.randrange(5)
        slots([rng.choice(values[:2]) for _ in range(count)] + [(count, 3)])
    if op == 0x3A: slots([(target, rng.choice((3, 5))), (rng.choice(strings), 1)])
    if op == 0x9A: slots([(strings[5], 1), (rng.randrange(100), 3)])
    if op == 0x4E: slots([rng.choice(((target, 5), (strings[1], 1), (0, 3))), (strings[2], 1)])
    if op == 0x4F: slots([(target, rng.choice((3, 5))), (strings[4], 1), (123, 3)])
    if op in (0x1D, 0x3C): slots([(strings[4], 1), (123, 3)])
    if op in (0x1C, 0x41): slots([(strings[4], 1)])
    if op in (0x13, 0x21, 0x29):
        # Include underflow after converting the first operand.
        slots([(rng.choice(strings), 1) for _ in range(rng.randrange(3))])
    if op in (0x47, 0x48, 0x49, 0x67):
        pair = [rng.choice(values), rng.choice(values)]
        if any(tag <= 1 for _, tag in pair):
            pair = [rng.choice(values[:4]), rng.choice(values[:4])]
        slots(pair)
    if op in (0x14, 0x31, 0x32, 0x36): slots([rng.choice(values[:4])])
    if op in (0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x29, 0x48, 0x49, 0x66, 0x67):
        boolean_slot = max(0, (initial if keep else 0) - (1 if op == 0x12 else 2))
    if boolean_slot is not None:
        t.ignore(STACK + boolean_slot * 8 + 1, 3)
    # Mixed programs check cursor movement and shared state across dispatches.
    sequence = rng.randrange(8)
    if sequence == 0:
        n = rng.randrange(1, 6)
        program = action(0x96, b"\x07" + struct.pack("<I", n))
        program += b"\x51\x4c" + action(0x9D, struct.pack("<h", -7)) + b"\x34"
        boolean_slot = None
    elif sequence == 1:
        program = action(0x88, struct.pack("<H", 2) + b"first\0second\0")
        program += action(0x96, b"\x08\x00\x09\x01\x00")
        program += action(0x87, b"\xff") + action(0x96, b"\x04\xff") + b"\x4d\x4c"
        boolean_slot = None
    elif sequence == 2:
        program = action(0x96, b"\x07" + struct.pack("<I", rng.getrandbits(32)) +
                         b"\x07" + struct.pack("<I", rng.getrandbits(32)))
        program += b"\x0a\x4c" + action(0x87, b"\x00") + b"\x62"
        boolean_slot = None
    # Ignore padding only if this is still the single boolean-producing action.
    if sequence <= 2 and t.ignored:
        t.ignored.clear()
    t.w32(DEPTH, initial)
    # Put a sentinel after Return's end pointer as well as at the stream's end.
    program += b"\0" + b"\0" * 16
    code = t.alloc(len(program), "bytecode", fill=program)
    bounded = rng.randrange(2)
    length = rng.choice((1, len(program) - 16)) if bounded else 0
    if op == 0x3E and sequence > 2: length = len(program) - 16
    t.args(r3=code, r4=target, r5=context, r6=length,
           r7=rng.choice((0, registers)), r8=(rng.getrandbits(24) << 8) | keep)
