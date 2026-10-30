"""Three row-major products and the current-viewport upload boundary.

Full 4x4 inputs (including non-affine w), identity/zero/sparse/cancellation,
VMX denormal flushing, infinities and NaNs. Upload observes the whole viewport;
all writes and preservation of the other fields are compared. vmsum4fp uses
lift-check's double-accumulation model, not a hardware precision measurement.
"""
from liftcheck.spec import *

FUNCTION = "grcViewport::RebuildCompositeMatrices"
ADDRESS = 0x82153070
SOURCE = "src/game/camera/pong_camera.cpp"
TRIALS = 1000
EXTERNS = {"g_pCurrentViewport": 0x825EBAA0}
FP_CONTRACT = "off"
CALLS = {"grcViewportUploadMatrices": stub(ret="void", args=("r3",), deref={"r3": 0x390})}

SPECIAL = (0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x807FFFFF,
           0x00800000, 0x80800000, 0x7F7FFFFF, 0xFF7FFFFF,
           0x7F800000, 0xFF800000, 0x7FC12345)


def inputs(t):
    vp = t.alloc(0x390, "viewport", ctype="grcViewport")
    other = t.alloc(0x390, "otherViewport", ctype="grcViewport")
    offsets = (0x80, 0x1C0, 0x240, 0x2C0)
    for offset in offsets:
        t.floats(vp + offset, 16, -40, 40)
    mode = t.index % 8
    if mode in (1, 2):
        # One identity or zero factor at each position in the chain.
        offset = offsets[(t.index // 8) % 4]
        for i in range(16):
            t.wf32(vp + offset + 4 * i, float(mode == 1 and i % 5 == 0))
    elif mode == 3:
        # Asymmetric sparse matrices expose row/column/order mistakes.
        for n, offset in enumerate(offsets):
            for i in range(16):
                t.wf32(vp + offset + i * 4, float((n + 2) * (i + 1)) if i % 4 == (i // 4 + n) % 4 else 0.0)
    elif mode == 4:
        for offset in offsets:
            for i in range(16):
                t.w32(vp + offset + 4 * i, t.rng.choice(SPECIAL))
    elif mode == 5:
        # Keep tiny products observable: small inputs times large normal values.
        for offset, bits in zip(offsets, (0x007FFFFF, 0x7E800000, 0x3F800000, 0x3F800000)):
            for i in range(16):
                t.w32(vp + offset + 4 * i, bits if i % 5 == 0 else 0)
    elif mode == 6:
        for offset in offsets:
            for i in range(16):
                t.wf32(vp + offset + 4 * i, t.rng.choice((1.0000001192092896, -1.0, 16777216.0, -16777216.0, 0.00001)))
    t.w32(t.sym("g_pCurrentViewport"), (0, vp, other)[t.index % 3])
    t.args(r3=vp)
