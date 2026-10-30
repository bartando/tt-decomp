"""General 4x4 inverse, including sequential writes through overlapping buffers.

Run the real PPC determinant helper on both sides, checking its input pointer
and all 64 input bytes. Exercise projective and affine matrices, reflections,
permutations, scale/shear, singular and cancellation-sensitive inputs. Compare
all destination/source/guard memory without a float tolerance (the checker's
usual equality treats signed zeros and NaN payloads as equivalent). No ignored
bytes or modeled arithmetic. Inputs are finite; extreme exponents, input NaNs,
invalid pointers and FPSCR exception flags are outside this spec's scope.
"""
import struct

from liftcheck.spec import run

FUNCTION = "rage::mat44Inverse"
ADDRESS = 0x8223F140
SOURCE = "src/rage/math/mat44.cpp"
TRIALS = 1500
FP_CONTRACT = "off"
CALLS = {"rage::mat44Determinant": run(args=("r3",), deref={"r3": 64})}


def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def inputs(t):
    rng = t.rng
    storage = t.alloc(256, "matricesAndGuards")
    src = storage + 96
    dst = src + rng.choice([-64, 64, -64, 64, 0, -32, 32, -16, 16, -4, 4])
    m = [rng.uniform(-4, 4) for _ in range(16)]
    kind = rng.randrange(12)
    if kind < 3:
        pass  # General projective matrices: all 16 lanes matter.
    elif kind == 3:
        m = [0.0] * 16  # No singularity rejection: writes NaNs.
    elif kind == 4:
        m = [rng.choice([-1.0, 1.0]) if i % 5 == 0 else 0.0 for i in range(16)]
    elif kind == 5:
        m = [0.0] * 16
        for row, col in enumerate(rng.sample(range(4), 4)):
            m[row * 4 + col] = rng.choice([-1, 1]) * 2.0**rng.randrange(-8, 9)
    elif kind == 6:
        # Affine scale/shear plus translation, not necessarily orthonormal.
        m[3], m[7], m[11], m[15] = 0.0, 0.0, 0.0, 1.0
    elif kind == 7:
        # Exactly dependent rows and exactly representable products.
        m = [float(rng.randrange(-4, 5)) for _ in range(16)]
        m[4:8] = m[:4]
    elif kind == 8:
        # Near-dependent rows expose cancellation and FMA ordering.
        m[:4] = [f32(x) for x in m[:4]]
        m[4:8] = [f32(x + rng.choice([-1, 1]) * 2.0**-20) for x in m[:4]]
    elif kind == 9:
        scale = 2.0**rng.randrange(-6, 7)
        m = [x * scale for x in m]
    elif kind == 10:
        m = [0.0] * 16
        for i in range(4):
            m[i * 5] = rng.choice([-1, 1]) * 2.0**rng.randrange(-18, 19)
    else:
        # A singular matrix with nonzero cofactors also produces infinities.
        m = [1.0 if i % 5 == 0 else 0.0 for i in range(16)]
        m[rng.randrange(4) * 5] = 0.0

    for i in range(16):
        t.wf32(dst + 4 * i, rng.uniform(-100, 100))
    for i, value in enumerate(m):
        t.wf32(src + 4 * i, value)
    t.args(r3=dst, r4=src)
