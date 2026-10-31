"""0x82255D58: inertia assembly, backward/forward real virtuals, block inverse.

Execute original math dependencies; each lift is checked separately. Only each
inverse's undefined scratch fourth row in C padding is ignored (16 bytes/body).
All coefficient rows, other padding, input integrity and virtual calls compare.
"""
import struct
from liftcheck.spec import *
from liftcheck.machine import ARENA_BASE
from specs._articulated_force_inputs import inputs as tree_inputs
FUNCTION = 'phArticulatedCollider_5D58'
ADDRESS = 0x82255D58
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 300
FP_CONTRACT = 'off'
FTOL = 1e-99


def prepare(ctx):
    ctx.write(ctx.r(3) + 0x20, b'\0' * 4)
    ctx.ret()


def matrix(ctx):
    values = [ctx.rng.uniform(-0.02, 0.02) for _ in range(48)]
    for block in (0, 32):
        for axis in range(3):
            values[block + axis * 4 + axis] += 0.25
    ctx.write(ctx.r(4), struct.pack('>48f', *values))
    ctx.ret()


CALLS = {name: run() for name in (
    'phArticulatedBody_BuildInertia', 'phMatrix_RotateDiagonal',
    'phSpatialTensor_Copy', 'phSpatialTensor_Add', 'phSpatialTensor_Difference',
    'phSpatialTensor_Invert', 'phMatrix_InvertSymmetric',
    'phMatrix_Multiply3x3', 'rage::mat33ComposeInPlace', 'phMatrix_InvertRegularized')}
for i in range(8):
    for slot in (19, 20):
        CALLS[f'forceJoint{i}.vfn_{slot}'] = model(prepare)
    for slot in (21, 22):
        CALLS[f'forceJoint{i}.vfn_{slot}'] = model(matrix, args=('r3', 'r4'))


def inputs(t):
    tree_inputs(t)
    data = t.reg_args['r3']
    count = int.from_bytes(t.arena[data - ARENA_BASE + 4:data - ARENA_BASE + 8], 'big', signed=True)
    for i in range(max(1, count)):
        start = data - ARENA_BASE + 40 + 4 * i
        body = int.from_bytes(t.arena[start:start + 4], 'big')
        t.wf32(body + 0x70, t.rng.uniform(0.2, 4))
        t.floats(body + 0x80, 3, 0.5, 3)
        t.ignore(body + 0x3C0, 16)
