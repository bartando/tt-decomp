"""Non-orthonormal bases, zeros, nonfinite lanes and overlapping xyz output."""
from liftcheck.spec import *
CALLS = {'rage::mat33Orthonormalize': run(deref={'r3': 64}),
         'crt_asin': run(), 'crt_atan2': run(),
         0x82430BA8: run(args=('r4', 'f1'))}


def inputs(t):
    matrix = t.alloc(96, 'matrixAndGuards', floats=[(16, 16)]) + 16
    t.floats(matrix, 16, -4, 4)
    if t.index % 5 == 0:
        for row in range(3):
            for col in range(3):
                t.wf32(matrix + row * 16 + col * 4, 1. if row == col else 0.)
    elif t.index % 5 == 2:
        rows = ((0., 1., 0.), (-1., 0., 0.), (0., 0., 1.))
        for row in range(3):
            for col in range(3):
                t.wf32(matrix + row * 16 + col * 4, rows[row][col])
    elif t.index % 5 == 1:
        for row in range(3):
            for col in range(3):
                t.wf32(matrix + row * 16 + col * 4, 0.)
    elif t.index % 7 == 0:
        t.wf32(matrix + 4 * t.rng.randrange(12), t.pick((-0., 1e-40, float('inf'), float('nan'))))
    output = t.pick((matrix, matrix + 4, matrix + 32, matrix + 48,
                     t.alloc(48, 'anglesAndGuards', floats=[(16, 4)]) + 16))
    t.float_words.update(output + i * 4 for i in range(3))
    t.args(r3=matrix, r4=output)
