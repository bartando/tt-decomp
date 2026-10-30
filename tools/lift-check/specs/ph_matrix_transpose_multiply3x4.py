"""0x821181C8: in-place relative transform; xyz dot3 and input X bits in W.

General bases, translations, cancellation, self/partial aliasing, arbitrary
w lanes, subnormals and nonfinite values. No ignored bytes, FTOL=0; the
checker equates NaNs and signed zeros.
VMX rounding/flush follows lift-check's emulator, not console evidence.
"""
from liftcheck.spec import *

FUNCTION = "phMatrix_TransposeMultiply3x4"
ADDRESS = 0x821181C8
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    storage = t.alloc(192, "matricesAndGuards")
    dst = storage + 16
    src = rng.choice((storage + 96, dst, dst + 16, dst - 16))
    t.floats(storage, 48, -100, 100)
    if rng.randrange(4) == 0:
        t.w32(rng.choice((dst, src)) + 4 * rng.randrange(16),
              rng.choice((0, 0x80000000, 1, 0x807FFFFF, 0x00800000,
                          0x7F800000, 0xFF800000, 0x7FC00000)))
    kind = rng.randrange(8)
    if kind < 3:
        src = storage + 96
        # Directed cases isolate flushed inputs, flushed results and dot
        # cancellation; random finite sums would usually hide the tiny term.
        for row in range(4):
            for axis in range(3):
                t.wf32(dst + row * 16 + axis * 4, 0)
                t.wf32(src + row * 16 + axis * 4, 0)
        if kind == 0:
            t.w32(dst, 0x007FFFFF)
            t.wf32(src, 1e38)
        elif kind == 1:
            t.wf32(dst, 1e-20)
            t.wf32(src, 1e-20)
        else:
            for axis, value in enumerate((1e10, 1., -1e10)):
                t.wf32(dst + axis * 4, value)
                t.wf32(src + axis * 4, 1)
    t.args(r3=dst, r4=src)
