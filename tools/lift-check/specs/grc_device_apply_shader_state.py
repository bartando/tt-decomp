"""Shader binding, cached vertex patches, depth state and command-buffer packets.

Limits: shader patch/copy helpers and cache flush are stubbed; this checks their
arguments (including metadata and the program-control in/out word), not their
implementations. Buffer rollover is modelled. The no-pixel-shader case must not
enter the final path that dereferences pixel metadata, matching the original's
caller invariant. Declarations have nonzero patch serials: the original's serial
allocation uses mtmsrd to guard lwarx/stwcx, which this emulator cannot execute.
That allocation/overflow path is lifted but not differentially checked. All
output memory, packet words and 64-bit dirty masks compare exactly.
"""
from liftcheck.spec import *

FUNCTION = "grcDevice_ApplyShaderState"
ADDRESS = 0x82363500
SOURCE = "src/graphics/grc_gpu_resources.cpp"
TRIALS = 1000


def rollover(ctx):
    cursor = ctx.alloc(0x400)
    ctx.write(ctx.r(3), cursor.to_bytes(4, "big"))
    limit = cursor + 4 * ctx.rng.choice([0, 1, 4, 8, 64])
    ctx.write(ctx.r(3) + 8, limit.to_bytes(4, "big"))
    ctx.ret(r3=cursor)


CALLS = {
    "rage_A980": model(rollover, args=("r3",)),
    "rage_2A68": stub(ret="void", args=("r3", "r4", "r5", "r6")),
    "rage_EEC0": stub(ret="void", args=("r3", "r4")),
    "rage_32F0": stub(ret="void", args=("r3", "r4", "r5", "r6", "r7", "r8", "r9"),
                      out={"r6": 4}, deref={"r6": 4, "r8": 0x20, "r9": 0x20}),
    "grc_3410": run(),
}


def inputs(t):
    rng = t.rng
    device = t.alloc(0x3500, "device")
    vertex = t.alloc(0x400, "vertexShader")
    pixel = t.alloc(0x100, "pixelShader") if rng.randrange(4) else 0
    declaration = t.alloc(0x80, "vertexDeclaration") if rng.randrange(4) else 0
    cursor = t.alloc(0x400, "commands")
    fence = t.alloc(4, "completedFence")
    t.w32(device, cursor)
    t.w32(device + 8, cursor + rng.choice([-4, 0, 4, 12, 256]))
    t.w32(device + 0x3294, vertex)
    t.w32(device + 0x3290, pixel)
    t.w32(device + 0x2C90, declaration)
    t.w32(device + 0x2890, fence)
    t.w32(fence, rng.choice([0, 1, 10, 100, 0xFFFFFFFF]))
    t.w32(device + 0x289C, rng.choice([0, 1, 10, 100, 0xFFFFFFFF]))
    t.w32(vertex + 8, rng.choice([0, 1, 10, 100, 0xFFFFFFFF]))
    t.w32(vertex + 0x24C, rng.choice([0, 0x80000000, t.u32()]))
    t.w32(vertex + 0x28, rng.choice([0, 0x1000, 0x8F000000, 0xBFFFFFFF, t.u32()]))
    t.w32(vertex + 0x258, rng.choice([0, 4, 128, 0xFFFFFFFC, t.u32()]))
    vertex_offset = rng.choice([0, 0x40, 0x80])
    t.w32(vertex + 0x264, vertex_offset)
    vertex_info = vertex + 0x250 + vertex_offset
    interface = rng.choice([0, 1, 0x1F, 0x7FFFF, t.u32()])
    t.w32(vertex_info + 0x10, interface)
    if pixel:
        pixel_offset = rng.choice([0, 0x20, 0x60])
        t.w32(pixel + 0x48, pixel_offset)
        pixel_info = pixel + 0x34 + pixel_offset
        # Do not overlap the offset field with metadata (offset zero is valid).
        t.w32(pixel_info + 0x10, interface ^ rng.choice([0, 0, 1, 0x20, 0x80000]))
        t.w32(pixel + 0xC, rng.choice([0, 1, 0x8F000000, 0xBFFFFFFF, t.u32()]))
        t.w32(pixel + 0x3C, rng.choice([0, 4, 128, t.u32()]))
        t.w32(pixel_info, rng.choice([0, 0x08000000, 0x10000000, 0x20000000, t.u32()]))
        t.w32(pixel_info + 0x1C, rng.choice([0, 0x10, 0x20, 0x30]))
    t.w32(vertex_info, rng.choice([0, 0x10000000, 0x20000000, t.u32()]))

    # Often force the fast/cached routes; unconstrained interface words would
    # almost always select the copy/repatch helper instead.
    dirty = rng.choice([0, 0x20, 0x80, 0x100, 0x120, 0x180, 0x1E0])
    t.w64(device + 0x30, rng.getrandbits(32) << 32 | dirty)
    t.w64(device + 0x28, rng.getrandbits(64))
    t.w8(device + 0x28C1, rng.choice([0, 0, 1, 8, 9, 0xF6]))
    t.w8(device + 0x28C2, rng.choice([0, 0x20, 0x80, 0xA0, 0xFF]))
    t.w8(device + 0x28C0, rng.choice([0, 0x20, 0xFF]) if pixel else 0)
    t.w32(device + 0x28A0, rng.choice([0, 0x100, t.u32() | 0x100]))
    t.w32(device + 0x2D94, (t.u32() & ~7) | rng.randrange(8))
    t.w32(device + 0x3298, rng.randrange(8))
    t.w32(device + 0x32A0, rng.choice([0, t.u32()]))
    # Enumerate depth comparisons and stencil write combinations, including
    # the rare early-depth/event branch and the late-depth flag path.
    depth = rng.randrange(8) << 4 | rng.choice([0, 2, 3, 6, 7, 0x83, 0x87])
    depth |= rng.choice([0, 0, 0x800, 0x20000, 0x800000, 0x20000000])
    t.w32(device + 0x2D74, depth)
    t.w32(device + 0x2D80, rng.choice([0, 1, 0x10, 0x11, t.u32()]))
    t.w32(device + 0x2D7C, rng.choice([0, 8, t.u32()]))
    if declaration:
        serial = rng.choice([1, 42, 0xFFFFFFFF])
        t.w32(declaration + 0x20, serial)
        t.w32(vertex + 0xC, rng.choice([serial, serial, t.u32()]))
        for offset in (0, 8):
            state = rng.getrandbits(64)
            t.w64(device + 0x3190 + offset, state)
            t.w64(vertex + 0x18 + offset, state ^ rng.choice([0, 0, rng.getrandbits(64)]))
            t.w64(declaration + 0x10 + offset, rng.choice([0, 0xFFFFFFFFFFFFFFFF, rng.getrandbits(64)]))
    t.w32(0x8271A83C, rng.choice([0, 1, 0xFFFFFFFD, 0xFFFFFFFE, 0xFFFFFFFF, t.u32()]))
    t.args(r3=device)
