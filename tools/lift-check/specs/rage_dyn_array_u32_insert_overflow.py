"""DynArrayU32::InsertOverflow (0x8222D278): STLport vector<4-byte T>::_M_insert_overflow."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "DynArrayU32::InsertOverflow"
ADDRESS = 0x8222D278
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"

CALLS = {
    "xe_EC88": alloc(size_reg="r3"),          # operator new
    "rage_free_00C0": stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    size = rng.choice([0, 1, 2, 5, rng.randrange(20)])
    cap = size + rng.choice([0, 1, 3])
    v = t.alloc(12, "vec")
    base = 0 if size == 0 and cap == 0 and rng.random() < 0.5 else t.alloc(4 * max(cap, 1), "data")
    t.w32(v + 0, base)
    t.w32(v + 4, base + 4 * size)
    t.w32(v + 8, base + 4 * cap)
    pos = base + 4 * rng.choice([0, size, rng.randrange(size + 1)])
    value = t.alloc(4, "value")
    fill = rng.choice([0, 1, 2, 7, rng.randrange(30)])
    t.args(r3=v, r4=pos, r5=value, r6=t.alloc(4, "tag"), r7=fill, r8=rng.choice([0, 1]))
