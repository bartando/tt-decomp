"""rage_strDuplicate (0x820C29E0): operator new(strlen + 1) and copy; null passes through."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage_strDuplicate"
ADDRESS = 0x820C29E0
SOURCE = "src/rage/data/at_types.cpp"

CALLS = {0x820DEC88: alloc(size_reg="r3")}


def inputs(t):
    if t.rng.random() < 0.15:
        t.args(r3=0)
        return
    n = t.rng.choice([0, 1, 5, 30])
    s = t.alloc(n + 1, "text", fill=bytes(t.rng.randrange(1, 256) for _ in range(n)) + b"\0")
    t.args(r3=s)
