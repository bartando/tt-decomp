"""0x82111EA0: in-place Y rotation of rows0/2, all four lanes and double angle.

Run the original cos/sin and CRT helpers. Keep row1, translation and guards;
cover signed zeros, subnormals and cancellation at exact float boundaries.
Finite inputs avoid overflow; FP exception flags are outside this proof.
"""
from liftcheck.spec import *
from specs.rage_cos_sin import angle

FUNCTION = "rage::mat33RotateY"
ADDRESS = 0x82111EA0
SOURCE = "src/rage/math/mat33.cpp"
TRIALS = 1000
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
    kind = t.index % 5
    if kind == 0:
        for row in range(3):
            for lane in range(4):
                t.wf32(matrix + row * 16 + lane * 4, float(row == lane))
    elif kind == 1:
        for row in (0, 2):
            for lane in range(4):
                t.wf32(matrix + row * 16 + lane * 4, rng.choice((0., -0., 2.**-149, -2.**-140, 2.**-126)))
    elif kind == 2:
        for lane in range(4):
            value = rng.uniform(-10, 10)
            t.wf32(matrix + lane * 4, value)
            t.wf32(matrix + 32 + lane * 4, value + 2.**-20)
    t.args(r3=matrix, f1=angle(rng))
