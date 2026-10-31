"""0x82257A30: r6 output, sequential aliased skew, angular composition and linear sum.

Only the three final W words read from undefined retail stack scratch are ignored;
the lift preserves those destination padding words. All xyz, inputs and guards compare.
"""
from liftcheck.spec import *
from specs._articulated_single_response_inputs import tree, vector
FUNCTION = 'phArticulatedCollider_GetPointResponseMatrix'
ADDRESS = 0x82257A30
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 600
FTOL = 1e-99
FP_CONTRACT = 'off'
CALLS = {'rage::mat33ComposeInPlace': run()}


def inputs(t):
    data, array, target = tree(t)
    output = t.alloc(80, 'matrixAndGuards', floats=[(16, 12)]) + 16
    point = vector(t, 'point')
    if t.index % 3 == 0:
        output = array[target] + t.rng.choice((0x10, 0x30, 0x50))
    if t.index % 4 == 0:
        point = output + t.rng.choice((0, 16, 32))
    for row in range(3):
        t.ignore(output + row * 16 + 12, 4)
    t.args(r3=data, r4=target, r5=point, r6=output)
