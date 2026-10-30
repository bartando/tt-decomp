"""Aligned command-data allocation, callback ABI and post-call state changes.

Cover sticky failure, null/success returns, count overflow, callback-adjusted
byte counts, unsigned accounting overflow and threshold equality, suppressors,
and both ring-reset paths. Callback state is deliberately different from entry
state. Compare all device bytes and callback entry snapshots; no ignores.
The reserve callback is modelled; allocation internals are outside this spec.
Ground truth: disasm/sections/.text.s, 0x8235A088..0x8235A14C.
"""
from liftcheck.spec import model

FUNCTION = "grcDevice_AllocateCommandData"
ADDRESS = 0x8235A088
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1000

_expected = None
_updates = None
_return = 0
_entry = None


def reserve(ctx):
    context, device, count, alignment = _expected
    assert (ctx.r(3), ctx.r(4), ctx.r(5), ctx.r(7)) == (context, device, 1, alignment)
    assert ctx.read(ctx.r(6), 4) == ((count * 4) & 0xffffffff).to_bytes(4, "big")
    assert ctx.read(device, 0x3800) == _entry, "device changed before reserve"
    ctx.write(ctx.r(6), _updates[0].to_bytes(4, "big"))
    for offset, value, size in _updates[1]:
        ctx.write(device + offset, value.to_bytes(size, "big"))
    ctx.ret(r3=_return)


CALLS = {"reserve": model(reserve, args=("r3", "r4", "r5", "r6", "r7"), deref={"r6": 4})}


def inputs(t):
    global _expected, _updates, _return, _entry
    r = t.rng
    device = t.alloc(0x3800, "device")
    context = t.alloc(16, "reserveContext")
    count = r.choice((0, 1, 6, 21, 0x3fffffff, 0x40000000, 0xffffffff, t.u32()))
    alignment = r.choice((1, 4, 16, 32, 128, 4096))
    t.w32(device + 0x3544, t.fake_fn("reserve"))
    t.w32(device + 0x3548, context)
    t.w8(device + 0x28c1, (t.index % 5 == 0) * 0x80 | r.randrange(128))
    adjusted = r.choice((0, 4, 16, 0xfffffffc, t.u32()))
    used = r.choice((0, 0xffffffff, 0xfffffffc, t.u32()))
    total = (used + adjusted) & 0xffffffff
    limit = (total + (-1, 0, 1)[t.index % 3]) & 0xffffffff
    secondary, start = t.u32(), t.u32()
    updates = [(0x36d0, used, 4), (0x36d4, limit, 4),
               (0x34e0, (0, 1, 0x80000000)[(t.index // 3) % 3], 4),
               (0, r.choice((0, 0xffffff80, t.u32())), 4),
               (0x36c8, secondary, 4),
               (0x36b4, secondary if t.index % 2 else secondary ^ 4, 4),
               (0x36b8, start, 4), (0x28c1, r.randrange(128), 1)]
    _updates = adjusted, updates
    _expected = context, device, count, alignment
    _return = 0 if t.index % 3 == 0 else t.alloc(32, "commandData")
    _entry = bytes(t.arena[:0x3800])
    t.args(r3=device, r4=count, r5=alignment)
