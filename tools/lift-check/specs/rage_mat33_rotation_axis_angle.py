"""0x820C3DA0: build a 3x3 rotation in three 16-byte rows from angle + axis.

Run the original axis/Rodrigues helpers and sin/cos; compare helper selection,
angle/sign and all four normalized lanes as well as matrix, padding and guards.
Cover zero angle (including null axis), +/- coordinate axes of arbitrary length,
zero axis, general unnormalized axes, tiny/huge axes and unordered/infinite axes.
Angles include non-float32 doubles. FTOL=0, no ignored bytes or code patches.
Inputs are aligned, output is disjoint from axis. Estimate instructions use the
checker's true reciprocal sqrt; actual console estimate bits and FP exception
flags are outside this differential proof. Memory/snapshots compare bit-for-bit;
float call arguments use the checker's NaN/signed-zero equality.
"""
from liftcheck.spec import *

FUNCTION = "rage::mat33RotationAxisAngle"
ADDRESS = 0x820C3DA0
SOURCE = "src/rage/math/mat33.cpp"
TRIALS = 1200
FP_CONTRACT = "off"

CALLS = {
    0x820C3F10: run(args=("r3", "f1")),
    0x820C3F98: run(args=("r3", "f1")),
    0x820C4020: run(args=("r3", "f1")),
    0x820C40A8: run(args=("r3", "r4", "f1"), deref={"r4": 16}),
    0x824302B0: run(args=("f1",)),
    0x824301D8: run(args=("f1",)),
}


def inputs(t):
    rng = t.rng
    storage = t.alloc(80, "matrixAndGuards", floats=[(16, 12)])
    out = storage + 16
    axis = t.alloc(16, "axis")
    kind = rng.randrange(18)
    angle = rng.choice((rng.uniform(-12, 12), 0.12500000000000003, -3.141592653589793))
    vector = [rng.uniform(-100, 100) for _ in range(4)]
    if kind in (0, 1):
        angle = 0.0 if kind == 0 else -0.0
    elif 2 <= kind <= 7:
        vector[:3] = [0.0, -0.0, 0.0]
        vector[(kind - 2) // 2] = rng.uniform(0.1, 100) * (-1 if kind & 1 else 1)
    elif kind == 8:
        vector[:3] = [0.0, -0.0, 0.0]  # falls through to negative Z
    elif kind == 9:
        vector[:3] = [2.0**-100, -2.0**-110, 2.0**-105]  # dot underflows
    elif kind == 10:
        vector[:3] = [2.0**-149, -2.0**-148, 0.0]  # scalar != 0, VMX == 0
    elif kind == 11:
        vector[:3] = [2.0**100, -2.0**101, 2.0**99]  # dot overflows
    elif kind == 12:
        vector[:3] = [0.0, 0.0, float("nan")]  # unordered Z flips the angle
    elif kind == 13:
        vector[:3] = [0.0, float("nan"), 0.0]
    elif kind == 14:
        vector[:3] = [float("nan"), 0.0, 0.0]
    elif kind == 15:
        vector[:3] = [float("inf"), -float("inf"), 1.0]
    elif kind == 16:
        vector[:3] = [0.0, 0.0, rng.choice((float("inf"), -float("inf")))]
    vector[3] = rng.choice((rng.uniform(-1000, 1000), 2.0**-149, float("nan"), float("inf")))
    for lane, value in enumerate(vector):
        t.wf32(axis + lane * 4, value)
    t.args(r3=out, r4=0 if kind == 0 else axis, f1=angle)
