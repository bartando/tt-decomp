"""0x820C3AD8: affine composition, early translation store and raw x-to-w merge.

Aligned and low-bit-offset pointers, all 16-byte overlaps in either direction,
nonorthogonal bases, arbitrary w bits, cancellation, signed zero, subnormal
inputs/results. Exact memory comparison, no stubs, ignored bytes or tolerance.
Finite xyz only; NaN arithmetic payloads and hardware FP flags are outside scope.
"""
FUNCTION = 'rage::mat44ComposeAffineInPlace'
ADDRESS = 0x820C3AD8
SOURCE = 'src/rage/math/mat44.cpp'
TRIALS = 1000
FP_CONTRACT = 'off'


def inputs(t):
    storage = t.alloc(256, 'matrices and guards')
    matrix = storage + 96
    source = matrix + t.pick([-64, -48, -32, -16, 0, 16, 32, 48, 64])
    for i in range(64):
        value = t.pick([0.0, -0.0, 1e-40, -1e-40, 1e-30, 1e30,
                        1.0 + t.rng.randrange(16) * 2**-20, t.f32(-8, 8)])
        t.wf32(storage + 4 * i, value)
    # W lanes participate only in translation and the mask forcibly replaces it.
    for row in range(4):
        t.w32(source + row * 16 + 12, t.u32())
    for lane in range(4):
        t.w32(0x82619BE0 + lane * 4, 0xFFFFFFFF if lane < 3 else 0)
        t.w32(0x82619BD0 + lane * 4, 0 if lane < 3 else 0x3F800000)
    t.args(r3=matrix + t.rng.randrange(16), r4=source + t.rng.randrange(16))
