"""Matrix-to-quaternion conversion at 0x8223B218.

Check all four dominant components, ties, unordered comparisons, arbitrary
non-orthogonal matrices, and overlapping float-aligned input/output buffers.
The sole callee executes its real fsqrt; no stubbed math or ignored writes.
Limits: default FP rounding mode; FPSCR exception flags and NaN sign/payload
are not compared. Finite cases compare every output bit, including signed zero.
NaN-diagonal cases compare NaNs numerically; no infinity inputs are generated.
"""
import math

from liftcheck.spec import *

FUNCTION = "LocomotionStateAnim_B218_g"
ADDRESS = 0x8223B218
SOURCE = "src/anim/locomotion.cpp"
TRIALS = 2000
# Enable numerical NaN comparison, below the smallest float32 difference.
# Only outputs of the deliberately NaN-diagonal cases are marked as floats.
FTOL = 1e-100
CALLS = {"rage::phBoundCapsule_01D0_g": run()}


def inputs(t):
    rng = t.rng
    block = t.alloc(160, "buffers")
    matrix = block + 32
    t.floats(matrix, 12, -10, 10)
    case = rng.randrange(11)
    if case < 4:
        # Real rotations, including identity and 180 degrees about each axis.
        q = [rng.uniform(-1, 1) for _ in range(4)]
        if case < 2:
            q = [0.0] * 4
            q[rng.randrange(4)] = 1.0
        length = math.sqrt(sum(v * v for v in q))
        x, y, z, w = [v / length for v in q]
        rows = [1 - 2 * (y*y + z*z), 2 * (x*y + z*w), 2 * (x*z - y*w), 0,
                2 * (x*y - z*w), 1 - 2 * (x*x + z*z), 2 * (y*z + x*w), 0,
                2 * (x*z + y*w), 2 * (y*z - x*w), 1 - 2 * (x*x + y*y), 0]
        for i, value in enumerate(rows):
            t.wf32(matrix + 4 * i, value)
    elif case < 7:
        # Dominance ties and trace equality, with both signed zeros.
        diagonals = rng.choice([
            (0, 0, 0), (-1, -1, -1), (1, 0, 0), (0, 1, 0), (0, 0, 1),
            (1, 1, -1), (1, -1, 1), (-1, 1, 1), (0.0, -0.0, -0.0),
            (-1, -1, 1), (-1, 1, -1), (1, -1, -1),
        ])
        for i, value in zip((0, 5, 10), diagonals):
            t.wf32(matrix + 4 * i, value)
    elif case < 10:
        # Subnormals and large finite values. Avoid overflow in trace/addition.
        bits = [0, 0x80000000, 1, 0x80000001, 0x007FFFFF, 0x00800000,
                0x6F7FFFFF, 0xEF7FFFFF, 0x3F800000, 0xBF800000]
        for i in range(12):
            t.w32(matrix + 4 * i, rng.choice(bits))
        if case == 7:
            # A NaN in any diagonal makes every result NaN. Both signs and
            # noncanonical payloads exercise the unordered comparison paths.
            for i in rng.sample((0, 5, 10), rng.randrange(1, 4)):
                t.w32(matrix + 4 * i, rng.choice([0x7FC00000, 0xFFC12345]))
    # Other cases keep unrestricted, non-orthogonal finite matrices.

    # Include exact aliasing, each row, preceding output, and partial overlap.
    out = matrix + rng.choice([-24, -12, -4, 0, 4, 8, 12, 16, 20, 24,
                              28, 32, 36, 40, 44, 48, 64])
    t.float_words.clear()
    if case == 7:
        t.float_words.update(out + 4 * i for i in range(4))
    t.args(r3=out, r4=matrix)
