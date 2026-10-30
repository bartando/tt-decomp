from liftcheck.spec import *

FUNCTION = "grcTextureFactoryXenon_EFE8"
ADDRESS = 0x8214EFE8
SOURCE = "src/graphics/texture_reference.cpp"
TRIALS = 1000
EXTERNS = {"_g_binkVideoPlayer": 0x825EB988, "g_grcFormatId": 0x825C9030}
CALLS = {
    "grcDevice_SetRenderTarget": stub(ret="void", args=("r3", "r4", "r5")),
    "grcDevice_SetViewport": stub(ret="void", args=("r3", "r4"), deref={"r4": 24}),
}

def inputs(t):
    device = t.alloc(0x3220, "device")
    surface = t.alloc(32, "surface")
    t.w32(EXTERNS["_g_binkVideoPlayer"], device)
    t.w32(EXTERNS["g_grcFormatId"], t.rng.choice([0x1a220197, 0, t.u32()]))
    t.floats(device + 0x3218, 2, -3, 3)
    t.args(r3=t.rng.randrange(4), r4=surface)
