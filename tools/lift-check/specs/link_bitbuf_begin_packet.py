"""datBitBuffer packet header (0x82238AE0): three 16-bit fields on an empty buffer."""
# Inputs keep a block and room to write: with no buffer, or the cursor at the
# limit, the original writes through a pointer from an uninitialised stack slot.
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "datBitBuffer_BeginPacket"
ADDRESS = 0x82238AE0
SOURCE = "src/rage/net/dat_bit_buffer.cpp"

def _allocate(ctx):
    ctx.ret(r3=0 if ctx.rng.random() < 0.1 else ctx.alloc(ctx.r(4)))


CALLS = {
    "datBitBuffer_Grow": run(),
    "datBitBuffer_WriteU32": run(),
    "datBitBuffer_WriteS32": run(),
    "datBitBuffer_BeginPacket": run(),
    "alloc.vfn_2": model(_allocate),
    "alloc.vfn_3": stub(ret="void"),
}


def make_buffer(t):
    rng = t.rng
    bb = t.alloc(0x28, "bb", fill="zero")
    allocator = t.alloc(8, "allocator", fill="zero")
    t.w32(allocator, t.vtable("alloc", 4))
    t.w32(bb + 0x24, allocator)
    max_bits = rng.choice([128, 256, 1000, rng.randrange(128, 4096)])
    size = rng.randrange(0, max_bits - 80)
    t.w32(bb + 0x10, size)
    t.w32(bb + 0x14, max_bits)
    t.w32(bb + 0x18, rng.choice([0, 0, rng.randrange(8)]))
    kind = rng.choice(["own", "own", "shared"])
    if kind == "none":
        t.w32(bb + 0x0C, 0)
    else:
        cap_bytes = (size + 7) // 8 + rng.choice([0, 1, 8, 64])
        block = t.alloc(4 + cap_bytes + 8, "block")  # m_bitOffset can reach a byte past capacity
        t.w32(block, 1 if kind == "own" else rng.choice([2, 3]))
        t.w32(bb + 0x00, block)
        t.w32(bb + 0x04, block + 4)
        t.w32(bb + 0x08, block + 4)
        t.w32(bb + 0x0C, cap_bytes * 8)
    return bb, max_bits, size


def inputs(t):
    rng = t.rng
    bb, max_bits, size = make_buffer(t)
    if rng.random() < 0.4:
        t.w32(bb + 0x10, 0)   # an empty buffer gets a header
    cursor = rng.choice([0, size, 48, rng.randrange(0, size + 1)])
    t.w32(bb + 0x20, cursor)
    t.w32(bb + 0x1C, rng.randrange(0, 64))
    bits = rng.choice([1, 4, 8, 16, 32, rng.randrange(0, 33)])
    t.args(r3=bb)
