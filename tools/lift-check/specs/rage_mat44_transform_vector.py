"""Four-lane vector transform, including sequential overlapping writes.

Finite inputs include general matrices, identity, zero and cancellation-prone
values. The guarded shared buffer covers overlap with the vector and matrix;
all written bytes are compared exactly, without a floating-point tolerance.
"""
FUNCTION = "rage::mat44TransformVector"
ADDRESS = 0x8223ECB0
SOURCE = "src/rage/math/mat44.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    storage = t.alloc(256, "buffer")
    matrix = storage + 64
    point = storage + 160
    out = rng.choice([storage + 208, point, point - 4, point + 4,
                      matrix, matrix + 4, matrix + 16, matrix + 48,
                      matrix - 4, matrix + 60])
    kind = rng.randrange(5)
    for i in range(16):
        value = rng.uniform(-20, 20)
        if kind == 0:
            value = 1.0 if i % 5 == 0 else 0.0
        elif kind == 1:
            value = 0.0
        elif kind == 2:
            value = rng.choice([-1.0, 1.0]) * (1.0 + rng.randrange(16) * 2**-20)
        t.wf32(matrix + 4 * i, value)
    for i in range(4):
        t.wf32(point + 4 * i, rng.uniform(-20, 20))
    t.args(r3=out, r4=point, r5=matrix)
