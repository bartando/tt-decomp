"""StlString::AllocateBlock (0x8222CEB8): STLport _String_base::_M_allocate_block(n)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "StlString::AllocateBlock"
ADDRESS = 0x8222CEB8
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"

CALLS = {
    "fiAsciiTokenizer_D588_g": alloc(size_reg="r4"),   # _M_allocate_block's allocate(proxy, n, hint)
}


def inputs(t):
    rng = t.rng
    s = t.alloc(0x18, "str")
    n = rng.choice([0, 1, 15, 16, 17, 18, 40, rng.randrange(200)])
    t.args(r3=s, r4=n)
