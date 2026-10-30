"""0x820D05A0: in-place X rotation of rows 1/2, all four lanes.

Execute the original cos/sin helper and CRT math; check angle and all external
writes, including preserved row 0, padding/guards and both changed w lanes.
Cover arbitrary/identity matrices, signed zero, cancellation and denormals.
FTOL=0, no ignored bytes. Inputs are aligned and finite, with no overflow;
VMX flush/round boundaries are observable, FP flags are outside this proof.
"""
from liftcheck.spec import *
from specs.rage_cos_sin import angle

FUNCTION = "rage::mat33RotateX"
ADDRESS = 0x820D05A0
SOURCE = "src/rage/math/mat33.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
CALLS = {
    0x820D04F0: run(args=("r3", "r4", "f1")),
    0x824302B0: run(args=("f1",)), 0x824301D8: run(args=("f1",)),
}


def inputs(t):
    rng = t.rng
    storage = t.alloc(96, "matrixAndGuards")
    matrix = storage + 16
    t.floats(matrix, 16, -100, 100)
    kind = rng.randrange(5)
    if kind == 0:
        for row in range(3):
            for lane in range(4):
                t.wf32(matrix + row * 16 + lane * 4, float(row == lane))
    elif kind == 1:
        for lane in range(4, 12):
            t.wf32(matrix + lane * 4, rng.choice((0., -0., 2.**-149, -2.**-140, 2.**-126)))
    elif kind == 2:
        for lane in range(4):
            value = rng.uniform(-10, 10)
            t.wf32(matrix + 16 + lane * 4, value)
            t.wf32(matrix + 32 + lane * 4, value + 2.**-20)
    t.args(r3=matrix, f1=angle(rng))
