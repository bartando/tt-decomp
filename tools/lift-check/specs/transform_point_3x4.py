"""86A8: affine xyz point transform; sequential stores and fused rounding.

Guarded storage checks only xyz are written and covers partial overlaps with
point and matrix, general/identity/zero/cancellation-prone matrices, and IEEE
special values. Exact comparison; no tolerance or ignored output bytes.
"""
FUNCTION = "TransformPoint3x4"
ADDRESS = 0x820E86A8
SOURCE = "src/game/camera/cm_cam_actions.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
SPECIAL = [0, 0x80000000, 0x7F800000, 0xFF800000, 0x7FC00000,
           0x00000001, 0x7F7FFFFF]


def inputs(t):
    rng = t.rng
    buf = t.alloc(256, "buffer")
    matrix, point = buf + 64, buf + 160
    out = rng.choice([buf + 208, buf + 208, point, point - 4, point + 4,
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
            value = rng.choice([-1.0, 1.0]) * (1 + rng.randrange(16) * 2**-20)
        t.wf32(matrix + 4 * i, value)
    t.floats(point, 4, -20, 20)
    if kind == 4:
        for base, n in ((matrix, 16), (point, 4)):
            t.w32(base + rng.randrange(n) * 4, rng.choice(SPECIAL))
    t.args(r3=out, r4=point, r5=matrix)
