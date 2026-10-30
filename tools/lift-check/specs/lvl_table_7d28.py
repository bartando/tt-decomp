"""0x82337D28: 32-wide indexed point filter, including rejected-slot writes.

The VMX inputs v1/v2 are mirrored in the portable entry's r7/r8 references.
Compare integer results and all memory exactly; no instruction patches or ignores.
Cover disjoint output and in-place compaction (the callers use disjoint buffers).
Arbitrary shifted overlaps with indices or points are outside this spec: the
original's interleaved loads/stores can expose its instruction scheduling there.
vmsum3fp128 uses lift-check's double-accumulation model; this does not establish
Xenon's intermediate precision for every adversarial rounding boundary.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "lvlTable_7D28_2h"
ADDRESS = 0x82337D28
SOURCE = "src/game/match/lvl_table.cpp"
FP_CONTRACT = "off"
TRIALS = 2000


def f32(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def rounded(value):
    return struct.unpack(">f", struct.pack(">f", value))[0]


def vector(t, name, values):
    addr = t.alloc(16, name)
    for i, value in enumerate(values):
        t.wf32(addr + i * 4, value)
    return addr


def inputs(t):
    rng = t.rng
    case = rng.randrange(24)
    count = rng.choice([-0x80000000, -32, -1, 0, 1, 31, 32, 33, 63, 64, 65, 96, 128])
    padded = ((max(0, count) + 31) // 32) * 32
    points = t.alloc(64 * 16, "points")
    indices = t.alloc(max(16, padded * 4), "indices")
    output = indices if case % 4 == 0 else t.alloc(max(16, padded * 4), "output")
    origin = [rng.uniform(-10, 10) for _ in range(4)]
    limit = [rng.uniform(1, 300)] * 4
    anchor = [rounded(rng.uniform(-20, 20)) for _ in range(4)]

    # Boundaries use exactly representable xyz differences with squared length 9.
    if case < 12:
        origin = [0.0] * 4
        limit = [[float("inf")] * 4, [-1.0] * 4, [9.0] * 4,
                 [f32(0x41100001)] * 4, [f32(0x410FFFFF)] * 4,
                 [10.0, 10.0, 10.0, 9.0], [10.0, float("nan"), 10.0, 10.0],
                 [float("nan")] * 4, [f32(1)] * 4, [f32(0x00800000)] * 4,
                 [0.0, -0.0, 0.0, -0.0], [1.0] * 4][case]
    elif case == 12:
        origin[0] = float("nan")
    elif case == 13:
        origin[2] = float("inf")
    elif case == 14:
        # The w coordinate must have no effect, even if unordered.
        origin[3] = float("nan")
    elif case == 15:
        limit = [rng.uniform(-2, 300) for _ in range(4)]
    elif case == 16:
        origin = [f32(0x00800001), 0.0, 0.0, 0.0]
        limit = [f32(1)] * 4
    elif case == 17:
        origin = [0.0] * 4
        limit = [float("inf")] * 4
    elif case >= 19:
        # Match one candidate's dot exactly, then move the strict threshold one
        # float32 ulp either way. No float tolerance can hide a changed decision.
        origin = [rounded(x) for x in origin]
        delta = [rounded(anchor[i] - origin[i]) for i in range(3)]
        distance = rounded(sum(x * x for x in delta))
        bits = struct.unpack(">I", struct.pack(">f", distance))[0]
        limit = [f32(bits + rng.choice([-1, 0, 1]))] * 4

    for i in range(64):
        values = [rng.uniform(-20, 20) for _ in range(4)]
        if case < 8:
            values = [1.0, 2.0, 2.0, float("nan")]
        elif case in (8, 9, 10):
            # DAZ on input, FTZ on the squared distance, and signed zero.
            values = [rng.choice([f32(1), f32(0x807FFFFF), f32(0x1A000000), -0.0]), 0.0, 0.0, 99.0]
        elif case == 11:
            values = [float(i % 2), 0.0, 0.0, float("inf")]
        elif case == 16:
            # Subtract two normal floats to produce a subnormal difference.
            values = [f32(0x00800000), 0.0, 0.0, 0.0]
        elif case == 17:
            values = [rng.choice([f32(0x7F7FFFFF), float("inf"), float("nan"), 1.0]), 0.0, 0.0, 0.0]
        elif case == 18:
            # Varied finite exponents exercise accumulation/rounding.
            values = [f32(rng.randrange(0x00800000, 0x7F800000)) for _ in range(4)]
        elif case >= 19 and i % 2 == 0:
            values = anchor
        for lane, value in enumerate(values):
            t.wf32(points + 16 * i + 4 * lane, value)

    for i in range(padded):
        # Scale-to-byte-offset drops high bits, but the stored index keeps them.
        index = rng.randrange(64) | (rng.randrange(16) << 28)
        t.w32(indices + i * 4, index)
    lim = vector(t, "distanceLimitSq", limit)
    org = vector(t, "origin", origin)
    if count <= 0:
        points = indices = output = lim = org = 0  # no pointer reads on this path
    t.args(r3=count, r4=points + (rng.randrange(16) if count > 0 else 0),
           r5=indices, r6=output, r7=lim, r8=org, v1=limit, v2=origin)
