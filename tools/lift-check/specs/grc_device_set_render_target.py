"""Colour target bind: release order, format conversion, tiling and write masks.

Samples all four slots, five binding shapes and all sixteen surface formats.
Randomizes mode/shift boundaries, reference-release conditions, preserved bits,
colour masks and each of the five tiled-target mismatch positions. No ignored
memory: both the device and every surface are compared, as are call arguments
and surface contents at the release and target-size callbacks.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_SetRenderTarget"
ADDRESS = 0x82356290
SOURCE = "src/graphics/grc_device.cpp"
TRIALS = 1000
CALLS = {
    0x82352708: stub(ret="void", args=("r3",), deref={"r3": 8}),
    0x823536E8: stub(ret="void", args=("r3", "r4"), deref={"r4": 56}),
}


def surface(t, name, fmt):
    s = t.alloc(0x40, name)
    t.w32(s, t.rng.choice([
        0x80000, 0x100000, 0x80001, 0x80100, 0x90000,
        0, 0xFFF80000, t.u32(),
    ]))
    t.w32(s + 52, (t.u32() & ~0xF0000) | (fmt << 16))
    return s


def inputs(t):
    rng = t.rng
    case = rng.randrange(4 * 5 * 16)
    slot = case % 4
    binding = (case // 4) % 5
    fmt = (case // 20) % 16
    dev = t.alloc(0x3500, "device")
    old = surface(t, "previous", fmt)
    new = surface(t, "surface", fmt)
    # New bind, replacement, same-surface rebind, unbind, already unbound.
    old, new = [(0, new), (old, new), (old, old), (old, 0), (0, 0)][binding]
    targets = [rng.choice([0, t.u32()]) for _ in range(4)]
    targets.append(rng.choice([0, surface(t, "depth", rng.randrange(16))]))
    targets[slot] = old
    after = targets.copy()
    after[slot] = new
    mismatch = rng.randrange(7)  # five mismatches, plus two all-match cases
    for i, target in enumerate(targets):
        t.w32(dev + 12536 + i * 4, target)
        cached = after[i]
        if i == mismatch:
            cached ^= 0x100
        elif target == 0 and rng.randrange(2):
            cached = t.u32()  # null bound targets must not invalidate tiling
        t.w32(dev + 12976 + i * 4, cached)
    for offset in (32, 40):
        t.w64(dev + offset, rng.choice([0, rng.getrandbits(64)]))
    t.w32(dev + 10396, t.u32())
    t.w8(dev + 10432, rng.randrange(256))
    t.w32(dev + 12960, rng.choice([0, 0, 0, t.u32()]))
    t.w32(dev + 12144 + slot * 4, rng.choice([
        0, 1, 2, 3, 15, 16, 31, 32, 33, 0xFFFFFFFF, t.u32(),
    ]))
    t.w32(dev + 11956 + slot * 4, rng.choice([0, 15, t.u32()]))
    t.args(r3=dev, r4=slot, r5=new)
