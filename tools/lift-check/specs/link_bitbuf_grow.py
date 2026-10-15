"""datBitBuffer::Grow (0x82260CE8): copy-on-write growth through the allocator."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "datBitBuffer_Grow"
ADDRESS = 0x82260CE8
SOURCE = "src/rage/net/dat_bit_buffer.cpp"


def _allocate(ctx):
    ctx.ret(r3=0 if ctx.rng.random() < 0.1 else ctx.alloc(ctx.r(4)))


CALLS = {
    "alloc.vfn_2": model(_allocate),
    "alloc.vfn_3": stub(ret="void"),
}


def make_buffer(t):
    rng = t.rng
    bb = t.alloc(0x28, "bb", fill="zero")
    allocator = t.alloc(8, "allocator", fill="zero")
    t.w32(allocator, t.vtable("alloc", 4))
    t.w32(bb + 0x24, allocator)
    max_bits = rng.choice([0, 64, 256, 1000, rng.randrange(1, 4096)])
    size = rng.randrange(0, max(1, max_bits + 1))
    t.w32(bb + 0x10, size)
    t.w32(bb + 0x14, max_bits)
    t.w32(bb + 0x18, rng.choice([0, 0, rng.randrange(8)]))
    kind = rng.choice(["none", "own", "own", "shared"])
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
    bits = rng.choice([0, size, size + 1, max_bits, max_bits + 1, rng.randrange(0, max_bits + 2)])
    t.args(r3=bb, r4=bits)
