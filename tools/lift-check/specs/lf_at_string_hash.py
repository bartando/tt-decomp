"""PJW string hash over signed chars (0x8223A818)."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage_atStringHash"
ADDRESS = 0x8223A818
SOURCE = "src/rage/data/at_types.cpp"


def inputs(t):
    n = t.rng.choice([0, 1, 7, 20])
    s = t.alloc(n + 1, "text", fill=bytes(t.rng.randrange(1, 256) for _ in range(n)) + b"\0")
    t.args(r3=s)
