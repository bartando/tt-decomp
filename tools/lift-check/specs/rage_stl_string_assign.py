"""fiAsciiTokenizer_SetString (0x8222CFA8): STLport basic_string::_M_assign(first, last).

The original returns the string in r3; the lift returns void (rage_par.cpp declares it
so), hence RET = None.
"""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "fiAsciiTokenizer_SetString"
ADDRESS = 0x8222CFA8
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"
RET = None

CALLS = {
    "StlString::Append": run(),                        # 0x8222D5E8, checked by stl_string_append
    "fiAsciiTokenizer_D588_g": alloc(size_reg="r4"),
    "game_DD78_h": run(),
    "rage_free_00C0": stub(ret="void"),
}


def text(rng, n):
    return bytes(rng.randrange(32, 127) for _ in range(n))


def inputs(t):
    rng = t.rng
    s = t.alloc(0x18, "str")
    size = rng.choice([0, 1, 5, 14, 15, rng.randrange(40)])
    if size < 16 and rng.random() < 0.5:
        for i, b in enumerate(text(rng, 16)):
            t.w8(s + i, b)
        t.w32(s + 0x10, s + size)
        t.w32(s + 0x14, s + 16)
    else:
        cap = size + rng.choice([0, 1, 3, 20])
        block = t.alloc(cap + 1, "heapbuf", fill=text(rng, cap + 1))
        t.w32(s + 0x00, block)
        t.w32(s + 0x10, block + size)
        t.w32(s + 0x14, block + cap + 1)
    n = rng.choice([0, 1, size, max(size - 1, 0), size + 1, rng.randrange(64)])
    src = t.alloc(max(n, 1), "src", fill=text(rng, max(n, 1)))
    t.args(r3=s, r4=src, r5=src + n)
