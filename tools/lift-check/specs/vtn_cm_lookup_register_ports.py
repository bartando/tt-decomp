"""cmLookup::RegisterPorts (0x8226D840): cache entry 0's value port (+0x1C/+0x20):
type 1 reads the data object's byte +0x10, type 2 the node's +4, else 0;
stored at +4. Checks the layout without the C++ vptr."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "cmLookup::RegisterPorts"
ADDRESS = 0x8226D840
SOURCE = "src/game/misc/cm_operators.cpp"
RET = None


def inputs(t):
    obj = t.alloc(0x44, "cmLookup")
    t.w32(obj + 0x1C, t.alloc(0x20, "src"))
    t.w32(obj + 0x20, t.rng.choice([0, 1, 2, 3]))
    t.args(r3=obj)
