"""Billboard emission, including rotated axes and the null-cursor count pass.

Exercises disjoint UV/output buffers, the 512-entry axis cache, asymmetric UVs,
signed and zero extents, scalar subnormals, angle-bin boundaries, negative wraps,
fctiwz saturation/NaN, UV-index shift overflow, and vertex-count overflow.
Camera/rotation setup is input state; the emitter has no semantic callees.
"""
import math
import struct

from liftcheck.spec import *

FUNCTION = "liftcheck_billboard_adapter"
ADDRESS = 0x82410058
SOURCE = "tools/lift-check/specs/fx_draw_billboard_quad_adapter.cpp"
TRIALS = 600
RET = None
FP_CONTRACT = "off"


def f32(value):
    return struct.unpack(">f", struct.pack(">f", value))[0]


def inputs(t):
    rng = t.rng
    # Guard bytes and random pre-existing vertices catch stride/extra writes.
    output = t.alloc(4 * 36 + 32, "vertices", floats=[
        (16 + corner * 36 + offset, count)
        for corner in range(4) for offset, count in [(0, 6), (28, 2)]])
    count_only = rng.choice([0, 1, 0xFFFFFFFF])
    cursor = 0 if count_only and rng.randrange(3) == 0 else output + 16
    t.w32(0x825EBA74, cursor)
    t.w32(0x825EBA84, count_only)
    t.w32(0x825EBA88, rng.choice([0, 1, 0xFFFFFFFE, rng.getrandbits(32)]))

    uv = t.alloc(16 * 16, "uv_rects")
    t.floats(uv, 64, -2.0, 2.0)
    t.w32(0x825C2B10, uv)
    uv_index = rng.randrange(16) | (rng.randrange(16) << 28)

    # Distinct entries expose phase sign, mask, scale and 32-byte stride errors.
    axes = [rng.uniform(-2.0, 2.0) for _ in range(512 * 8)]
    t.put(0x82715FD0, struct.pack(">4096f", *axes))
    t.floats(0x82715FB0, 8, -2.0, 2.0)

    phase = rng.choice([0, 1, 255, 256, 511, 512, 513, 1023, rng.randrange(-4096, 4096)])
    boundary = f32(phase * math.tau / 512)
    angle = rng.choice([0.0, -0.0, boundary, -boundary,
                        f32(boundary + 1e-5), f32(boundary - 1e-5),
                        rng.uniform(-100, 100), 1e30, -1e30,
                        math.inf, -math.inf, math.nan])
    tiny = struct.unpack(">f", bytes.fromhex("00000001"))[0]
    values = [f32(rng.uniform(-100, 100)) for _ in range(5)]
    for k in range(5):
        if rng.randrange(4) == 0:
            values[k] = rng.choice([0.0, -0.0, tiny, -tiny, 1.0, -1.0, 1e30, -1e30])
    t.args(r3=uv_index, r10=rng.getrandbits(32), f1=f32(angle),
           **{f"f{k + 2}": f32(value) for k, value in enumerate(values)})
