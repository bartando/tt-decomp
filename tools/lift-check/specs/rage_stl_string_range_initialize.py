"""StlString::RangeInitialize (0x8222D480): STLport basic_string::_M_range_initialize."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "StlString::RangeInitialize"
ADDRESS = 0x8222D480
SOURCE = "src/rage/io/fiAsciiTokenizer.cpp"

CALLS = {
    "StlString::AllocateBlock": run(),                 # 0x8222CEB8, checked by its own spec
    "fiAsciiTokenizer_D588_g": alloc(size_reg="r4"),
}


def inputs(t):
    rng = t.rng
    s = t.alloc(0x18, "str")
    n = rng.choice([0, 1, 7, 14, 15, 16, 17, 40, rng.randrange(100)])
    src = t.alloc(max(n, 1), "src", fill=bytes(rng.randrange(32, 127) for _ in range(max(n, 1))))
    t.args(r3=s, r4=src, r5=src + n)
