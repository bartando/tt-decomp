"""xe_D850: construct static/quantized/raw channels and retain the smallest.

RTTI identifies the three vtables. Slot 8 initializes samples with a float
tolerance; slot 13 reports storage size; slot 0 destroys with a delete flag.
Model those callees independently so the factory must forward every argument,
write the exact constructor fields, mask status to a byte, and delete the loser.
Allocations succeed, as required by the original's unconditional dereferences.
"""
import struct

from liftcheck.spec import model, stub

FUNCTION = "rage::CreateFloatAnimChannel"
ADDRESS = 0x8224D850
SOURCE = "src/rage/animation/rage_anim.cpp"
TRIALS = 1000

VTABLES = {"static": 0x8204F8D4, "quantized": 0x8204F9AC, "raw": 0x8204F76C}
SIZES = {"static": 12, "quantized": 24, "raw": 16}
ENCODINGS = {"static": 4, "quantized": 6, "raw": 1}
_trial = {}


def _allocate(ctx, direct=False):
    k = _trial[ctx.side]["allocations"]
    kind = ("static", "quantized", "raw")[k]
    assert ctx.r(4 if direct else 3) == SIZES[kind], "wrong allocation size"
    if direct:
        assert k == 0 and ctx.r(3) == _trial["allocator"]
        assert ctx.r(5) == 16, "wrong alignment"
    else:
        assert k > 0, "static allocation must use the TLS allocator directly"
    _trial[ctx.side]["allocations"] += 1
    ctx.ret(r3=_trial["objects"][kind])


def _initialize(kind):
    def initialize(ctx):
        obj = _trial["objects"][kind]
        assert ctx.r(3) == obj
        assert ctx.read(obj, SIZES[kind]) == _trial["constructed"][kind], \
            f"incorrect {kind} constructor writes (including preserved bytes)"
        assert ctx.r(4) == _trial["samples"]
        assert ctx.r(5) == _trial["count"]
        assert ctx.r(6) == _trial["skip"]
        assert ctx.f(1) == _trial["tolerance"]
        # Opaque callee effects, identical on both sides, on poisoned storage.
        ctx.write(obj + 8, _trial["effects"][kind])
        ctx.ret(r3=_trial["status"][kind])
    return initialize


def _destroy(kind):
    def destroy(ctx):
        obj = _trial["objects"][kind]
        assert ctx.r(3) == obj and ctx.r(4) == 1, "wrong delete target/flag"
        deleted = _trial[ctx.side]["deleted"]
        assert obj not in deleted, "double delete"
        deleted.add(obj)
        ctx.write(obj + 5, b"\0")
    return destroy


def _size(kind):
    def size(ctx):
        obj = _trial["objects"][kind]
        assert ctx.r(3) == obj and obj not in _trial[ctx.side]["deleted"]
        ctx.ret(r3=_trial["sizes"][kind])
    return size


INIT_ARGS = ("r3", "r4", "r5", "r6", "f1")
CALLS = {
    0x820C0038: stub(ret="void", args=()),
    "allocator.vfn_1": model(lambda c: _allocate(c, direct=True), args=("r3", "r4", "r5")),
    0x820DEC88: model(_allocate, args=("r3",)),
    0x822465A0: model(_initialize("static"), args=INIT_ARGS, deref={"r4": 16}),
    0x822479B0: model(_initialize("quantized"), args=INIT_ARGS, deref={"r4": 16}),
    0x82245650: model(_initialize("raw"), args=INIT_ARGS, deref={"r4": 16}),
    0x82244040: model(_destroy("static"), args=("r3", "r4")),
    0x82244AA0: model(_destroy("quantized"), args=("r3", "r4")),
    0x82244180: model(_destroy("raw"), args=("r3", "r4")),
    0x82247B00: model(_size("quantized"), args=("r3",)),
    0x822461F8: model(_size("raw"), args=("r3",)),
}


def inputs(t):
    rng = t.rng
    # Static success, quantized failure, either winner, ties, and signed-size
    # boundaries. Everything comes from t.rng so --only N reproduces trial N.
    case = rng.randrange(8)
    high = lambda: rng.randint(1, 0xFFFFFF) << 8
    status = {
        "static": high() | (rng.choice([1, 2, 0x80, 0xFF]) if case == 0 else 0),
        "quantized": high() | (0 if case == 1 else rng.choice([1, 2, 0x80, 0xFF])),
        "raw": high() | rng.choice([0, 1, 0x80, 0xFF]),
    }
    n = rng.randint(1, 0x10000)
    qsize, rsize = [
        (n, n), (n, n), (n, n + 1), (n + 1, n), (n, n),
        (0xFFFFFFFF, 0), (0, 0x80000000), (0x80000000, 0x7FFFFFFF),
    ][case]
    _trial.update(status=status, sizes={"quantized": qsize, "raw": rsize},
                  objects={}, constructed={}, effects={},
                  orig={"allocations": 0, "deleted": set()},
                  lift={"allocations": 0, "deleted": set()})

    sda = t.alloc(0x10, "sda")
    thread = t.alloc(0x10, "thread")
    allocator = t.alloc(0x10, "allocator")
    t.w32(allocator, t.vtable("allocator", 3))
    t.w32(thread + 4, allocator)
    t.w32(sda, thread)
    t.w32(0x82600000, sda)  # g_sda_base represents r13 in the lift.
    _trial["allocator"] = allocator

    for kind, size in SIZES.items():
        # Guards and untouched constructor fields stay random, not zero-filled.
        storage = rng.randbytes(size + 32)
        obj = t.alloc(size + 32, kind, fill=storage) + 16
        expected = bytearray(storage[16:16 + size])
        expected[:4] = struct.pack(">I", VTABLES[kind])
        expected[5] = ENCODINGS[kind]
        if kind != "static":
            expected[8:16] = bytes(8)
        _trial["objects"][kind] = obj
        _trial["constructed"][kind] = bytes(expected)
        _trial["effects"][kind] = rng.randbytes(size - 8)

    count = rng.choice([0, 1, 2, 3, 4, 31, 256, 65535])
    skip = rng.choice([0, 1, 2, 3, 7, 15])
    samples = t.alloc(max(16, count * (skip + 1) * 4), "samples")
    tolerance = struct.unpack(">f", struct.pack(">f", rng.choice([
        0.0, -0.0, 1e-6, 0.125, -0.5, rng.uniform(-100, 100),
    ])))[0]
    _trial.update(samples=samples, count=count, skip=skip, tolerance=tolerance)
    # r3 is ignored by the factory; callers pass their DOF/channel container.
    t.args(r3=t.u32(), r4=samples, r5=count, r6=skip, f1=tolerance, r13=sda)
