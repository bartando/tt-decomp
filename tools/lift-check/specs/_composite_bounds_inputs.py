"""Sparse composite parts, non-rigid matrices and mutable SIMD initialization.

Includes empty lists, null holes, negative/reflected scales, unordered values,
subnormals, a child alias of the owner, and zero-distance reciprocal-root paths.
No ignored memory; the CRT square root executes its original/lifted body.
"""
from liftcheck.spec import *

CALLS = {'crt_sqrt': run(),
         'rage::phBoundComposite_RebuildExtents': run(),
         'rage::phBoundComposite_ComputeRadius': run(),
         'pongCreatureInst_F3E0_v12': stub(ret='void', args=('r3',), deref={'r3': 0x84})}


def inputs(t):
    obj = t.alloc(0xc0, 'compositeAndGuards') + 16
    t.floats(obj + 8, 18, -8, 8)
    count = t.pick((0, 1, 2, 3, 5, 8))
    parts = t.alloc(max(4, count * 4), 'partPointers')
    matrices = t.alloc(max(64, count * 64), 'partMatrices', floats=[(0, max(16, count * 16))])
    for i in range(count):
        child = t.alloc(0x70, 'partAndGuards') + 16
        t.floats(child + 8, 14, -10, 10)
        if t.index % 11 == 0 and i == 0:
            child = obj
        if t.index % 9 == 0 or t.rng.randrange(5) == 0:
            child = 0
        t.w32(parts + i * 4, child)
        matrix = matrices + i * 64
        t.floats(matrix, 16, -3, 3)
        if t.index % 5 == 0:
            for k in range(16):
                t.wf32(matrix + k * 4, 1. if k in (0, 5, 10, 15) else 0.)
        if child and t.index % 7 == 0:
            for lane in range(4):
                t.wf32(child + 0x30 + lane * 4, 0.)
        if child and t.index % 13 == 0:
            t.w32(child + t.pick((8, 0x10, 0x20, 0x30, 0x34, 0x38, 0x3c)),
                  t.pick((1, 0x807fffff, 0x7f800000, 0xff800000, 0x7fc00000, 0x80000000)))
    t.w16(obj + 0x82, count)
    t.w32(obj + 0x70, parts)
    t.w32(obj + 0x78, matrices)
    center = t.pick((obj + 0x30, t.alloc(16, 'queryCenter')))
    t.floats(center, 4, -5, 5)
    if t.index % 7 == 0:
        for lane in range(4):
            t.wf32(center + lane * 4, 0.)
    mode = t.index % 4
    for lane in range(4):
        t.w32(t.sym('lbl_82619BE0') + lane * 4, (0xffffffff if lane < 3 else 0) if mode else 0)
        t.w32(t.sym('lbl_82619BD0') + lane * 4, 0x3f800000 if mode and lane == 3 else 0)
        t.wf32(t.sym('lbl_82619BF0') + lane * 4, t.pick((0., float('inf'))))
    t.args(r3=obj, r4=matrices, r5=center)
    return obj
