"""Fixtures for spatial tensors and scalar inertia helpers."""
def tensor_pair(t):
    out = t.alloc(448, 'destinationAndGuards') + 16
    source = t.alloc(224, 'sourceAndGuards') + 16
    t.floats(out, 104, -10, 10)
    t.floats(source, 48, -10, 10)
    if t.index % 3 == 0:
        source = out + t.rng.choice((0, 16, 64, 192))
    if t.index % 5 == 0:
        t.w32(t.rng.choice((out, source)) + 4 * t.rng.randrange(12),
              t.rng.choice((1, 0x807FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000)))
    t.args(r3=out, r4=source)


def multiply(t):
    out = t.alloc(256, 'multiplyArena') + 16
    left = t.alloc(96, 'leftAndGuards') + 16
    right = t.alloc(96, 'rightAndGuards') + 16
    t.floats(out, 56, -10, 10)
    t.floats(left, 16, -10, 10)
    t.floats(right, 16, -10, 10)
    if t.index % 3 == 0:
        left = out + t.rng.choice((0, 16, 64))
    if t.index % 4 == 0:
        right = out + t.rng.choice((0, 16, 64))
    t.args(r3=out, r4=left, r5=right)


def inverse_symmetric(t):
    source = t.alloc(96, 'symmetricAndGuards') + 16
    out = t.alloc(96, 'inverseAndGuards') + 16
    t.floats(source, 16, -2, 2)
    t.floats(out, 16, -2, 2)
    for i in (0, 5, 10):
        t.wf32(source + i * 4, t.rng.uniform(5, 10))
    if t.index % 7 == 0:
        for i in (0, 4, 5, 8, 9, 10):
            t.wf32(source + i * 4, 0.)
    if t.index % 3 == 0:
        out = source
    t.args(r3=source, r4=out)


def inverse_regularized(t):
    source = t.alloc(160, 'stridedMatrixAndGuards') + 16
    t.floats(source, 32, -3, 3)
    stride = t.rng.choice((3, 4, 5, 8))
    for i in (0, stride + 1, 2 * stride + 2):
        t.wf32(source + i * 4, t.rng.choice((0., 1e-8, -0.1, 5., 10.)))
    t.args(r3=source, r4=stride)


def rotate_diagonal(t):
    r = t.alloc(96, 'rotationAndGuards') + 16
    d = t.alloc(96, 'diagonalAndGuards') + 16
    out = t.alloc(96, 'outputAndGuards') + 16
    t.floats(r, 16, -3, 3)
    t.floats(d, 16, -3, 3)
    t.floats(out, 16, -3, 3)
    if t.index % 3 == 0:
        out = t.rng.choice((r, d))
    t.args(r3=r, r4=d, r5=out)


def body_inertia(t):
    body = t.alloc(0x480, 'bodyAndGuards') + 16
    t.floats(body, 0x460 // 4, -4, 4)
    t.wf32(body + 0x70, t.rng.uniform(0.1, 5))
    t.args(r3=body)


def invert_tensor(t):
    source = t.alloc(224, 'inputTensorAndGuards') + 16
    out = t.alloc(224, 'inverseTensorAndGuards') + 16
    t.floats(source, 48, -0.1, 0.1)
    t.floats(out, 48, -2, 2)
    for block in (0, 32):
        for row in range(3):
            t.wf32(source + 4 * (block + row * 4 + row), t.rng.uniform(2, 5))
        for row in range(3):
            for col in range(row):
                value = t.rng.uniform(-0.1, 0.1)
                t.wf32(source + 4 * (block + row * 4 + col), value)
                t.wf32(source + 4 * (block + col * 4 + row), value)
    # Original copies an uninitialized stack fourth row into output C padding.
    # Coefficient rows, every other W lane, and input integrity still compares.
    t.ignore(out + 0xB0, 16)
    t.args(r3=source, r4=out)
