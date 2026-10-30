"""Segment/polygon wrapper, including both triangle calls and hit record fields.

The helper is modeled to exercise all its return paths and output values; its
stack output pointers are read using each ABI's calling convention. Inputs are
aligned, disjoint, finite normal floats and valid 16-bit vertex indices.
"""
import struct
from liftcheck.spec import *

FUNCTION = "phPolygon_IntersectSegment"
ADDRESS = 0x822200C0
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 1000
FP_CONTRACT = "off"


def intersect(ctx):
    poly = ctx.r(6)
    indices = struct.unpack(">4H", ctx.read(poly + 16, 8))
    # The last vertex uniquely identifies the first and second calls.
    vertex_base = ctx.r(7) - 16 * indices[0]
    second = ctx.r(9) == vertex_base + 16 * indices[3] and indices[3] != indices[2]
    status = ctx.read(poly + (25 if second else 24), 1)[0]
    sp = ctx.m.gpr(1)
    offsets = (0x54, 0x5c) if ctx.side == "orig" else (8, 12)
    end_ptr, frac_ptr = (int.from_bytes(ctx.read(sp + n, 4), "big") for n in offsets)
    ctx.write(ctx.r(10), ctx.read(poly + 28, 4))
    ctx.write(end_ptr, ctx.read(poly + 28, 4))
    ctx.write(frac_ptr, ctx.read(poly + 32, 4))
    ctx.ret(r3=status)


CALLS = {"phBoundGeometry_DBC8_wrh": model(intersect,
    args=("r3", "r4", "r5", "r6", "r7", "r8", "r9"),
    deref={"r3": 16, "r4": 16, "r5": 16, "r6": 24, "r7": 16, "r8": 16, "r9": 16},
    preserves=("f1",))}


def inputs(t):
    rng = t.rng
    poly = t.alloc(36, "polygon")
    vertices = t.alloc(16 * 8, "vertices")
    segment = t.alloc(32, "segment")
    hit = t.alloc(80, "hit")
    for i in range(4): t.wf32(poly + 4*i, rng.choice([-2, -1, 0, 0.5, 1, 2]))
    t.w8(poly + 15, rng.randrange(256))
    for i, index in enumerate((1, 3, 5, rng.choice([0, 7]))): t.w16(poly + 16 + i*2, index)
    t.w8(poly + 24, rng.choice([0, 1, 2, 3, 4, 5, 255]))
    t.w8(poly + 25, rng.choice([0, 1, 4]))
    t.wf32(poly + 28, rng.choice([-2, -1, -0.0, 0.0, 0.5, 2]))
    fraction = rng.choice([-1, 0, 0.25, 0.5, 1, 2])
    t.wf32(poly + 32, fraction)
    for i in range(32): t.wf32(vertices + 4*i, rng.randint(-8, 8) * 0.25)
    for i in range(8): t.wf32(segment + 4*i, rng.randint(-8, 8) * 0.25)
    t.args(r3=poly, r4=vertices, r5=segment, r6=hit if rng.randrange(4) else 0,
           f1=rng.choice([fraction, -2, 0, 0.5, 1, 3]))
