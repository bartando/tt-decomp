"""DynArrayU32::operator= (0x8222D150): STLport vector<4-byte T>::operator=."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "DynArrayU32::operator="
ADDRESS = 0x8222D150
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"

CALLS = {
    # allocator<T>::allocate(proxy, count, hint): count elements of 4 bytes
    "fiAsciiTokenizer_76D8_g": stub(ret=lambda ctx: ctx.alloc(max(1, ctx.r(4) * 4))),
    "rage_free_00C0": stub(ret="void"),
}


def vec(t, name, size, cap, null_ok=True):
    v = t.alloc(12, name)
    if cap == 0 and null_ok and t.rng.random() < 0.5:
        base = 0
    else:
        base = t.alloc(4 * max(cap, 1), name + ".data")
    t.w32(v + 0, base)
    t.w32(v + 4, base + 4 * size)
    t.w32(v + 8, base + 4 * cap)
    return v


def inputs(t):
    rng = t.rng
    size = rng.choice([0, 1, 3, 8, rng.randrange(20)])
    cap = size + rng.choice([0, 0, 1, 4, rng.randrange(10)])
    this = vec(t, "this", size, cap)
    if rng.random() < 0.08:
        other = this
    else:
        osize = rng.choice([0, 1, size, max(size - 1, 0), size + 1, cap, cap + 1, rng.randrange(30)])
        other = vec(t, "other", osize, osize + rng.choice([0, 2]), null_ok=False)
    t.args(r3=this, r4=other)
