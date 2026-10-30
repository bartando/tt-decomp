"""0x820E8E28: table avoidance, inner box OR outer box clipped by a Y/Z slope.

Bounds are runtime globals, not immutable court constants (0x820E8CD8 updates
them). Vary them independently, including empty/reversed boxes, exact/adjacent
float32 faces and slope thresholds, flat Z, unordered values and subnormals.
No ignored writes, return masking or tolerance; original PPC is the oracle.
"""
import math
import struct

from liftcheck.spec import *

FUNCTION = "pongPlayer_IsInTableAvoidanceVolume"
ADDRESS = 0x820E8E28
SOURCE = "src/game/player/pong_player.cpp"
TRIALS = 1600
RET = "r3"
FP_CONTRACT = "off"

INNER_MIN, INNER_MAX = 0x82607240, 0x82607230
OUTER_MIN, OUTER_MAX = 0x82607210, 0x82607220


def f32(x):
    return struct.unpack(">f", struct.pack(">f", x))[0]


def adjacent(x, direction):
    if x == 0:
        return direction * 2.0**-149
    bits = struct.unpack(">I", struct.pack(">f", x))[0]
    bits += 1 if (x > 0) == (direction > 0) else -1
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def inputs(t):
    r = t.rng
    # Distinct extents catch swapped globals and use of inner instead of outer Y.
    lo = [-float(r.randrange(1, 10)), -float(r.randrange(1, 8)), -float(r.randrange(1, 8))]
    hi = [float(r.randrange(1, 10)), float(r.randrange(1, 8)), float(r.randrange(1, 8))]
    outer_lo = [lo[0] - 3, lo[1] - 2, hi[2]]
    outer_hi = [hi[0] + 5, hi[1] + 3, hi[2] + r.randrange(1, 12)]
    bounds = [lo, hi, outer_lo, outer_hi]
    mode = r.randrange(12)
    p = [(a + b) / 2 for a, b in zip(lo, hi)]
    if mode in (1, 2, 3, 4, 5):
        p = [(a + b) / 2 for a, b in zip(outer_lo, outer_hi)]
    if mode == 1:
        p[1] = outer_lo[1]  # accepted outer wedge
    elif mode == 2:
        p[1] = outer_hi[1]  # rejected by slope, within outer AABB
    elif mode == 3:
        # At and one float32 step either side of every box face.
        box_lo, box_hi = r.choice(((lo, hi), (outer_lo, outer_hi)))
        p = [(a + b) / 2 for a, b in zip(box_lo, box_hi)]
        axis = r.randrange(3)
        p[axis] = r.choice((box_lo, box_hi))[axis]
        direction = r.choice((-1, 0, 1))
        if direction:
            p[axis] = adjacent(p[axis], direction)
    elif mode == 4:
        # Match each single-precision instruction, then straddle the sloped face.
        p[2] = f32(r.uniform(outer_lo[2], outer_hi[2]))
        fraction = f32(f32(p[2] - outer_hi[2]) / f32(outer_lo[2] - outer_hi[2]))
        p[1] = f32(outer_hi[1] * fraction)
        direction = r.choice((-1, 0, 1))
        if direction:
            p[1] = adjacent(p[1], direction)
    elif mode == 5:
        outer_lo[2] = outer_hi[2]
        p[2] = outer_hi[2]
        p[1] = r.choice((outer_lo[1], 0.0, outer_hi[1], adjacent(outer_hi[1], 1)))
    elif mode in (6, 7):
        if r.random() < 0.5:
            p = [(a + b) / 2 for a, b in zip(outer_lo, outer_hi)]
            p[1] = outer_lo[1]
        if mode == 6:
            p[r.randrange(3)] = math.nan
        else:
            r.choice(bounds)[r.randrange(3)] = math.nan
    elif mode == 8:
        p[r.randrange(3)] = r.choice((-math.inf, math.inf))
        if r.random() < 0.5:
            r.choice(bounds)[r.randrange(3)] = p[r.randrange(3)]
    elif mode == 9:
        axis = r.randrange(3)
        box_lo, box_hi = r.choice(((lo, hi), (outer_lo, outer_hi)))
        box_lo[axis], box_hi[axis] = box_hi[axis], box_lo[axis]
    elif mode == 10:
        tiny = (0.0, -0.0, 2.0**-149, -2.0**-149, 2.0**-126)
        for b in bounds:
            b[:] = [r.choice(tiny) for _ in range(3)]
        p = [r.choice(tiny) for _ in range(3)]
    elif mode == 11:
        p = [r.uniform(-20, 20) for _ in range(3)]
    for addr, b in zip((INNER_MIN, INNER_MAX, OUTER_MIN, OUTER_MAX), bounds):
        for lane, value in enumerate(b):
            t.wf32(addr + 4 * lane, value)
        t.w32(addr + 12, t.u32())  # padding must not affect containment
    pos = t.alloc(32, "positionAndGuard")
    for lane, value in enumerate(p):
        t.wf32(pos + 4 * lane, value)
    t.args(r3=pos)
