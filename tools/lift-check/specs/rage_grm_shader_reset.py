"""grmShader::Reset (0x820F5350): clears the active-shader cell 0x825EBA68."""
from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "rage::grmShader::Reset"
ADDRESS = 0x820F5350
SOURCE = "src/rage/rage_grm.cpp"


def inputs(t):
    t.w32(0x825EBA68, t.rng.getrandbits(32))
    t.args(r3=t.alloc(0x28, "shader"))
