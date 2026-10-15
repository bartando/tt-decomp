"""XACT list append (0x8244C1A8, rage_C1A8): node from the pool, linked at the tail."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage_C1A8"
ADDRESS = 0x8244C1A8
SOURCE = "src/rage/core/rage_core_utils.cpp"

CALLS = {0x8244BDE0: model(lambda c: c.ret(r3=c.alloc(12) if c.rng.random() < 0.85 else 0))}


def inputs(t):
    lst = t.alloc(0xD8, "list")
    t.w32(lst + 0xD0, t.alloc(12, "tail") if t.rng.random() < 0.6 else 0)
    t.args(r3=lst, r4=t.u32())
