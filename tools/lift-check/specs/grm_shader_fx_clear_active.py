from liftcheck.spec import *

FUNCTION = "rage::grmShaderFx::ClearActive"
ADDRESS = 0x820EFAE8
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000
EXTERNS = {"g_grmShaderFx_activeState": 0x825EBA68, "g_grmShaderFx_activeInstance": 0x825EBC4C, "grmShaderInstance_Unbind": 0x82159CF0}
def unbind(ctx):
    state = int.from_bytes(ctx.read(EXTERNS["g_grmShaderFx_activeState"], 4), "big")
    instance = int.from_bytes(ctx.read(EXTERNS["g_grmShaderFx_activeInstance"], 4), "big")
    assert state == 0 and instance == ctx.r(3), "unbind must see cleared state and old instance"
    ctx.write(EXTERNS["g_grmShaderFx_activeInstance"], (0x12345678).to_bytes(4, "big"))


CALLS = {"grmShaderInstance_Unbind": model(unbind, args=("r3",))}


def inputs(t):
    t.w32(t.sym("g_grmShaderFx_activeState"), t.u32())
    t.w32(t.sym("g_grmShaderFx_activeInstance"), t.rng.choice((0, t.u32())))
    t.args(r3=t.alloc(32, "shader"))
