"""0x820C40A8: scalar Rodrigues rotation, three padded vec4 rows.

Execute CRT cos/sin; check double angle and call order, all nine matrix entries,
padding, source and guards with FTOL=0. Cover normalized and arbitrary axes,
coordinate/zero axes, cancellation and tiny components. The original reads
axis components between writes: aligned whole/partial source-output overlap
is included. Finite inputs avoid overflow; FP flags are outside this proof.
"""
import math
from liftcheck.spec import *
from specs.rage_cos_sin import angle

FUNCTION = "rage::mat33RotationNormalizedAxis"
ADDRESS = 0x820C40A8
SOURCE = "src/rage/math/mat33.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
CALLS = {0x824302B0: run(args=("f1",)), 0x824301D8: run(args=("f1",))}


def inputs(t):
    rng = t.rng
    storage = t.alloc(192, "matrixAxisAndGuards")
    out = storage + 64
    axis = out + rng.choice((-48, -16, 0, 16, 32, 64))
    t.floats(out, 12, -10, 10)
    vector = [rng.uniform(-5, 5) for _ in range(3)]
    kind = rng.randrange(6)
    if kind == 0:
        length = math.sqrt(sum(x*x for x in vector))
        vector = [x / length for x in vector]
    elif kind == 1:
        vector = [0., -0., 0.]
        vector[rng.randrange(3)] = rng.choice((-1., 1.))
    elif kind == 2:
        vector = [0., -0., 0.]
    elif kind == 3:
        vector = [rng.choice((-1, 1)) * 2.**rng.randrange(-140, -60) for _ in range(3)]
    for lane, value in enumerate(vector + [rng.uniform(-100, 100)]):
        t.wf32(axis + lane * 4, value)
    t.args(r3=out, r4=axis, f1=angle(rng))
