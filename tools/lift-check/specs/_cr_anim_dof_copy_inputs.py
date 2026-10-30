"""Raw-bit corpus shared by the two vfn_6 copy specs."""
from liftcheck.spec import model


# Keep these as words: converting signaling NaNs through Python floats quiets them.
PAYLOADS = (
    (0x00000000, 0x80000000, 0x80000000, 0x00000000),
    (0x7FC12345, 0xFFC54321, 0x7F800001, 0xFF800123),
    (0x7F800000, 0xFF800000, 0x7F7FFFFF, 0xFF7FFFFF),
    (0x00000001, 0x80000001, 0x007FFFFF, 0x807FFFFF),
    (0x00800000, 0x80800000, 0x00800001, 0x80800001),
    # Non-unit and negative quaternions must survive without normalization/flip.
    (0x40000000, 0xC0400000, 0x40800000, 0xC0A00000),
    (0xBF800000, 0x80000000, 0x00000000, 0x80000000),
    # (1 + 2^-23), (1 - 2^-23), -1: FMA-sensitive cancellation inputs.
    # vfn_6 must copy even these without performing any arithmetic.
    (0x3F800001, 0x3F7FFFFE, 0xBF800000, 0x33800000),
)


def source(ctx):
    ctx.ret(r3=int.from_bytes(ctx.read(ctx.r(3) + 4, 4), "big"))


def inputs(t, *, overlapping_pairs=False):
    rng = t.rng
    target = t.alloc(64, "target")
    source_obj = t.alloc(8, "source")
    payload = t.alloc(16, "sourcePayload")
    t.w32(source_obj, t.vtable("source"))
    aliases = (payload, payload, target + 16)
    if overlapping_pairs:
        # Quaternion ld/std pairs are ordered: source=target+8 propagates the
        # first pair into the second; a whole-16-byte snapshot is incorrect.
        aliases += (target + 8, target + 24)
    pointer = rng.choice(aliases)
    t.w32(source_obj + 4, pointer)
    words = rng.choice(PAYLOADS) if rng.randrange(4) else tuple(t.u32() for _ in range(4))
    for lane, word in enumerate(words):
        t.w32(pointer + 4 * lane, word)
    # w32 + FTOL=0 keeps comparison byte-exact, including NaN payloads, signaling
    # bits, subnormals and zero signs. Destination/neighbor bytes stay random.
    t.args(r3=target, r4=source_obj,
           f1=rng.choice((0.0, -0.0, -1.0, 0.5, 1.0, 2.0,
                          float("nan"), float("inf"), -float("inf"))))


def calls(slot):
    return {f"source.vfn_{slot}": model(source, args=("r3",))}
