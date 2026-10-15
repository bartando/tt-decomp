"""DynArrayMatrix34::InsertOverflow (0x8222D958): STLport vector<Matrix34>::_M_insert_overflow_aux."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "DynArrayMatrix34::InsertOverflow"
ADDRESS = 0x8222D958
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"

CALLS = {
    "xe_EC88": alloc(size_reg="r3"),           # operator new
    "fiAsciiTokenizer_DDD0_w": run(),          # uninitialized_copy<Matrix34>
    "rage_free_00C0": stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    size = rng.choice([0, 1, 2, 5, rng.randrange(10)])
    cap = size + rng.choice([0, 1, 3])
    v = t.alloc(12, "vec")
    base = 0 if size == 0 and cap == 0 and rng.random() < 0.5 else t.alloc(64 * max(cap, 1), "data")
    t.w32(v + 0, base)
    t.w32(v + 4, base + 64 * size)
    t.w32(v + 8, base + 64 * cap)
    pos = base + 64 * rng.choice([0, size, rng.randrange(size + 1)])
    value = t.alloc(64, "value")
    fill = rng.choice([0, 1, 1, 2, 5, rng.randrange(12)])
    t.args(r3=v, r4=pos, r5=value, r6=t.alloc(4, "tag"), r7=fill, r8=rng.choice([0, 1]))
