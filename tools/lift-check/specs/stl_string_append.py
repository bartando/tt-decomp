"""StlString::Append (STLport basic_string::_M_appendT): calls and memory."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "StlString::Append"
ADDRESS = 0x8222D5E8
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"

CALLS = {
    "fiAsciiTokenizer_D588_g": alloc(size_reg="r4"),   # _M_allocate_block(proxy, n, hint)
    "game_DD78_h": run(),                              # uninitialized_copy: run the original
    "rage_free_00C0": stub(ret="void"),
}


def inputs(t):
    rng = t.rng
    s = t.alloc(0x18, "str")
    size = rng.choice([0, 1, 5, 14, 15, rng.randrange(40)])
    if size < 16 and rng.random() < 0.5:
        # text in the 16-byte inline buffer
        t.w32(s + 0x10, s + size)
        t.w32(s + 0x14, s + 16)
    else:
        cap = size + rng.choice([0, 1, 3, 20])
        block = t.alloc(cap + 1, "heapbuf")
        t.w32(s + 0x00, block)
        t.w32(s + 0x10, block + size)
        t.w32(s + 0x14, block + cap + 1)
    n = rng.choice([0, 1, 2, 7, 16, rng.randrange(64)])
    src = t.alloc(max(n, 1), "src", fill=bytes(rng.randrange(32, 127) for _ in range(max(n, 1))))
    t.args(r3=s, r4=src, r5=src + n)
