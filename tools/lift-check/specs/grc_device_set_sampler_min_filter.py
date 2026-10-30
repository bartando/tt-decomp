"""Xenos sampler minification filter, shared anisotropy and volume overrides.

Device initialization (0x82366300) dispatches sampler state for slots 0..25;
also test raw slot values through 255 to cover srd's 63/64 and 127/128 edges.
The max-anisotropy byte is limited to 0..16, the 17-entry table's domain.
Filter values include the normal 0..4 range, individual bits and random u32s;
volume override bytes and all preexisting fetch/dirty bits are unrestricted.
No callees are stubbed and no memory is ignored. The table is read from the
game image, with some trials patching its entries to expose the exact masks.
This checks the shadow-state update, not GPU execution or rendered output.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_setSamplerMinFilter"
ADDRESS = 0x82355418
SOURCE = "src/graphics/grc_device.cpp"


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3800, "device")
    sampler = rng.choice([rng.randrange(26), rng.randrange(26), 0, 25, 31, 32,
                          63, 64, 65, 127, 128, 129, 255])
    filter_value = rng.choice([0, 1, 2, 3, 4, 5, 7, 8, 0xFFFFFFFF,
                               1 << rng.randrange(32), t.u32()])
    t.w8(device + 12020 + sampler, rng.randrange(17))
    t.w8(device + 12098 + sampler, rng.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 255,
                                             rng.randrange(256)]))

    # Include clean and saturated masks as well as random existing dirty bits.
    t.w64(device + 32, rng.choice([0, 0xFFFFFFFFFFFFFFFF, rng.getrandbits(64)]))
    if rng.randrange(2):
        for i in range(17):
            t.w32(0x82065D10 + 4 * i, t.u32())
    t.args(r3=device, r4=sampler, r5=filter_value)
