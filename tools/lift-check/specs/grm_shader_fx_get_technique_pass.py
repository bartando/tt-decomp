from liftcheck.spec import *

FUNCTION = "rage::grmShaderFx::GetTechniquePass"
ADDRESS = 0x820EF060
SOURCE = "src/rage/rage_grm.cpp"
TRIALS = 1000
EXTERNS = {"g_grmShaderFx_forcedVariantId": 0x825C9A5C,
           "g_grmShaderFx_variantTable": 0x825EBBD8,
           "g_grmShaderFx_defaultVariant": 0x825C9A64}

def inputs(t):
    r = t.rng
    obj = t.alloc(80, "shader")
    effect = t.alloc(520, "effect")
    techniques = t.alloc(1024, "techniques")
    slots = t.alloc(65536, "slots")
    entries = t.alloc(2052, "entries")
    mode = r.randrange(3)
    variant = r.randrange(16)
    t.w32(EXTERNS["g_grmShaderFx_forcedVariantId"], variant if mode == 0 else -1)
    t.w32(EXTERNS["g_grmShaderFx_variantTable"] + 4, 1 if mode == 1 else 0)
    t.w32(EXTERNS["g_grmShaderFx_defaultVariant"] - 4, variant if mode == 1 else r.randrange(16))
    t.w32(EXTERNS["g_grmShaderFx_defaultVariant"], variant if mode == 2 else r.randrange(16))
    for i in range(256):
        slot = r.randrange(512)
        t.w32(techniques + i*4, (slot << 18) | r.randrange(1 << 18))
        t.w32(slots + slot*4, entries + slot*4)
        t.w32(entries + slot*4 + 4, t.u32())
    t.w32(obj + 16, effect)
    t.w32(obj + 64, techniques)
    t.w32(effect + 512, slots)
    t.args(r3=obj, r4=r.randrange(64))
