"""In-place affine inverse; execute the real inverse callee on both sides.

General/sheared/reflected bases, translations, singular matrices, cancellation,
scales and adjacent float32 rejection thresholds. Arbitrary w-lane bits and
surrounding guards must survive; reject leaves all 64 bytes untouched. The call
trace compares the entire snapshot (including w lanes) and the bool return.
Finite xyz inputs, aligned matrix, default FP environment; no ignored bytes,
float tolerance, overflow or signaling NaNs in arithmetic lanes.
"""
import struct
from liftcheck.spec import *

FUNCTION = "rage::mat44InverseAffineInPlace"
ADDRESS = 0x820D7B30
SOURCE = "src/rage/math/mat44.cpp"
TRIALS = 1000
CALLS = {0x820D7B90: run(args=("r3", "r4"), deref={"r4": 64})}
RET = "r3"


def inputs(t):
    r = t.rng
    matrix = t.alloc(96, "matrixAndGuards") + 16
    m = [r.uniform(-8, 8) for _ in range(16)]
    kind = r.randrange(9)
    if kind == 1:
        m[:12] = [0.0] * 12
    elif kind in (2, 3, 4):
        bits = 0x34C14606 + r.choice([-2, -1, 0, 1, 2])
        epsilon = struct.unpack(">f", struct.pack(">I", bits))[0]
        m[:12] = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, epsilon * (-1 if kind == 3 else 1), 0]
        if kind == 4:
            m[10] = r.choice([-1, 1]) * 2.0**r.randrange(-12, 13)
    elif kind == 5:
        m[:3] = [float(r.randrange(-8, 9)) for _ in range(3)]
        m[4:7] = m[:3]
    elif kind == 6:
        scale = 2.0**r.randrange(-16, 17)
        m[:12] = [x * scale for x in m[:12]]
    elif kind == 7:
        m[4:7] = [x + r.choice([-1, 1]) * 2**-20 for x in m[:3]]
    for i, value in enumerate(m):
        if i % 4 == 3:
            t.w32(matrix + 4 * i, t.u32())
        else:
            t.wf32(matrix + 4 * i, value)
    t.args(r3=matrix, r4=0)
