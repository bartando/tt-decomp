"""DynArrayMatrix34::Resize (0x8222CD98): STLport vector<Matrix34>::resize(n, fill)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "DynArrayMatrix34::Resize"
ADDRESS = 0x8222CD98
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"

CALLS = {
    # The tag argument is an empty STLport __false_type on the stack (r7 here, r6 for
    # InsertOverflow): compare it as a stack pointer, but not its one indeterminate
    # byte (deref of 0 bytes turns lift-check's const-pointee comparison off).
    "fiAsciiTokenizer_DAF0_2h": stub(ret="void", deref={"r7": 0}),     # not lifted
    "DynArrayMatrix34::InsertOverflow": stub(ret="void", deref={"r6": 0}),   # own spec
}


def inputs(t):
    rng = t.rng
    size = rng.choice([0, 1, 2, 5, rng.randrange(12)])
    cap = size + rng.choice([0, 1, 3, 6])
    v = t.alloc(12, "vec")
    base = 0 if cap == 0 and rng.random() < 0.5 else t.alloc(64 * max(cap, 1), "data")
    t.w32(v + 0, base)
    t.w32(v + 4, base + 64 * size)
    t.w32(v + 8, base + 64 * cap)
    n = rng.choice([0, size, max(size - 1, 0), size + 1, cap, cap + 1, rng.randrange(20)])
    fill = t.alloc(64, "fill")
    t.args(r3=v, r4=n, r5=fill)
