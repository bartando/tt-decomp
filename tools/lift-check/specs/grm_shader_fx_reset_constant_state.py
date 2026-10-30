from liftcheck.spec import *

FUNCTION = "rage::grmShaderFx::ResetConstantState"
ADDRESS = 0x820EF9C8
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000
EXTERNS = {"g_grmShaderFx_activeInstance": 0x825EBC4C}

def inputs(t):
    obj = t.alloc(64, "shader")
    instance = t.alloc(560, "instance")
    t.w32(EXTERNS["g_grmShaderFx_activeInstance"], instance)
    t.args(r3=obj)
