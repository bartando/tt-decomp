"""Inclusive range wrap, signed arithmetic and word-overflow edges."""
from liftcheck.spec import *
FUNCTION = "math_WrapIndex"
ADDRESS = 0x820DC4E8
SOURCE = "src/rage/math/index_wrap.cpp"
TRIALS = 1000

def inputs(t):
    edge = [-2147483648, -2147483647, -100, -1, 0, 1, 2, 100, 2147483646, 2147483647]
    while True:
        value, low, high = [t.rng.choice(edge) if t.index < 500 else t.rng.randint(-2147483648, 2147483647) for _ in range(3)]
        length = (high - low + 1) & 0xffffffff
        offset = (value - low) & 0xffffffff
        if high <= low or (length and not (length == 0xffffffff and offset == 0x80000000)):
            break
    t.args(r3=value, r4=low, r5=high)
