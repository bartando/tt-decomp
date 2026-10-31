"""0x820C3BC8: VMX dot3 composition; raw X bits to W; translation untouched."""
from liftcheck.spec import *
FUNCTION = 'rage::mat33ComposeInPlace'
ADDRESS = 0x820C3BC8
SOURCE = 'src/rage/math/mat33.cpp'
TRIALS = 800
FP_CONTRACT = 'off'


def inputs(t):
    left = t.alloc(128, 'leftAndGuards') + 16
    right = t.alloc(96, 'rightAndGuards') + 16
    t.floats(left, 24, -20, 20)
    if t.index % 3 == 0:
        right = left + t.rng.choice((0, 16, 32))
    t.floats(right, 16, -20, 20)
    if t.index % 5 == 0:
        t.w32(t.rng.choice((left, right)) + 4 * t.rng.randrange(12),
              t.rng.choice((1, 0x807FFFFF, 0x7F800000, 0xFF800000, 0x7FC00000)))
    t.args(r3=left, r4=right)
