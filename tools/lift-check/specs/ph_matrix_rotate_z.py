"""0x82175D88: rotate both full vec4 XY basis rows by one double angle.

Execute the original cosine/sine helper and CRT callees. Nonsymmetric bases,
arbitrary w, rounding-sensitive inputs, subnormals and nonfinites. Rows Z and
translation and guards must survive. Exact comparisons, no ignored memory.
VMX flush/rounding follows the emulator. Written NaN payloads and zero signs
compare exactly.
"""
import math
from liftcheck.spec import *

FUNCTION = "phMatrix_RotateZ"
ADDRESS = 0x82175D88
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
CALLS = {0x820D04F0: run(args=("r3", "r4", "f1")),
         0x824302B0: run(args=("f1",)), 0x824301D8: run(args=("f1",))}


def inputs(t):
    rng = t.rng
    matrix = t.alloc(96, "matrixAndGuards") + 16
    t.floats(matrix, 16, -1000, 1000)
    if t.index % 4 == 0:
        t.w32(matrix + 4 * rng.randrange(8), rng.choice((
            0, 0x80000000, 1, 0x807FFFFF, 0x00800000,
            0x7F800000, 0xFF800000, 0x7FC00000)))
    angle = rng.choice((0., -0., math.pi / 2, -math.pi, 1 + 2**-30,
                        rng.uniform(-1000, 1000)))
    t.args(r3=matrix, f1=angle)
