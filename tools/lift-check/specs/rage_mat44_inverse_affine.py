"""Affine inverse, including the scalar routine's sequential overlap behavior.

Exercises general bases, reflections, scales, shear, singular/near-singular
matrices, and adjacent float32 values around the strict rejection boundary.
Source and destination can coincide or partially overlap in either direction.
All memory (including untouched w lanes, source and guards) and the bool return
are compared exactly. No calls are modeled, ignored bytes or float tolerance.
Inputs are finite; extreme overflow, NaN payload propagation and invalid pointers
are outside this spec's scope. W lanes contain arbitrary bits and must be ignored.
"""
import struct

FUNCTION = "rage::mat44InverseAffine"
ADDRESS = 0x820D7B90
SOURCE = "src/rage/math/mat44.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def inputs(t):
    rng = t.rng
    # Shared guarded storage also checks that no successful store hits a w lane.
    storage = t.alloc(256, "matricesAndGuards")
    src = storage + 96
    dst = src + rng.choice([0, 0, -64, 64, -32, 32, -16, 16, -4, 4])
    m = [rng.uniform(-8, 8) for _ in range(16)]
    kind = rng.randrange(12)
    if kind < 3:
        pass  # general nonorthogonal bases, both determinant signs
    elif kind == 3:
        m[:12] = [0.0] * 12
    elif kind in (4, 5):
        m[:12] = [1.0, 0.0, 0.0, 0.0,
                  0.0, -1.0 if kind == 5 else 1.0, 0.0, 0.0,
                  0.0, 0.0, 1.0, 0.0]
    elif kind == 6:
        # Exactly dependent rows, with exactly representable products.
        m[:3] = [float(rng.randrange(-8, 9)) for _ in range(3)]
        m[4:7] = m[:3]
        m[8:11] = [float(rng.randrange(-8, 9)) for _ in range(3)]
    elif kind in (7, 8):
        # det = +/-epsilon, max basis = 1. Hit equal and both neighboring ULPs.
        bits = 0x34C14606 + rng.choice([-2, -1, 0, 1, 2])
        epsilon = struct.unpack(">f", struct.pack(">I", bits))[0]
        m[:12] = [1.0, 0.0, 0.0, 0.0,
                  0.0, 1.0, 0.0, 0.0,
                  0.0, 0.0, epsilon * (-1 if kind == 8 else 1), 0.0]
    elif kind == 9:
        # Cancellation-sensitive determinant/cofactors, not just diagonal bases.
        row = [f32(rng.uniform(-2, 2)) for _ in range(3)]
        m[:3] = row
        m[4:7] = [f32(x + rng.choice([-1, 1]) * 2**-20) for x in row]
    elif kind == 10:
        # Permutations put the largest absolute element in every basis position.
        m[:12] = [0.0] * 12
        columns = rng.sample(range(3), 3)
        for row, column in enumerate(columns):
            m[row * 4 + column] = rng.choice([-1, 1]) * 2.0**rng.randrange(-12, 13)
    else:
        # Common scale matters: the test uses max element, not max cubed.
        scale = 2.0**rng.randrange(-16, 17)
        m[:12] = [x * scale for x in m[:12]]

    # Independently random initial output, especially the four untouched lanes.
    for i in range(16):
        t.wf32(dst + 4 * i, rng.uniform(-100, 100))
    for i, value in enumerate(m):
        if i % 4 == 3:
            t.w32(src + 4 * i, rng.getrandbits(32))
        else:
            t.wf32(src + 4 * i, value)
    t.args(r3=dst, r4=src)
