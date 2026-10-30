"""0x82340900: eight-wide cloth distance relaxation, formerly pongCreatureInst_0900.

Compare xyz writes, untouched memory, calls, and preserved registers against the
original instructions. No callees are stubbed. Mask ONLY referenced particles' w
words: the original initializes xyz at entry SP-0x160 but reads the uninitialized
fourth scratch word at SP-0x154 into its w arithmetic. This unused padding lane
has no portable value; the lift keeps the input w without changing its ABI.

Cover signed empty counts, padding to eight, multiple batches, batch snapshots,
duplicate/self endpoints and last-store order, full uint16 indices, position-base
rounding, compression/stretch/equality, unequal/zero/negative weights and strength,
non-affine w, zero denominators, NaN/Inf and VMX DAZ/FTZ. Constraint records are
aligned and disjoint from positions, with valid endpoints and allocated padding.
Limits: reciprocal is lift-check's exact vrefp model, dot3 accumulates in double;
console estimate bits and NaN payload/sign are unverified. No game integration.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "clothSolveDistanceConstraints"
ADDRESS = 0x82340900
SOURCE = "src/game/match/lvl_table.cpp"
FP_CONTRACT = "off"
TRIALS = 2000


def f32(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def vector(t, addr, values):
    for lane, value in enumerate(values):
        t.wf32(addr + 4 * lane, value)


def inputs(t):
    rng = t.rng
    case = rng.randrange(32)
    count = rng.choice((1, 2, 7, 8, 9, 15, 16, 17, 24, 25))
    if case == 0:
        count = rng.choice((-0x80000000, -9, -1, 0))
    padded = (max(0, count) + 7) & ~7
    # Guard records and particles remain random and fully compared.
    records = t.alloc(max(1, padded + 2) * 16, "constraints")
    particle_count = 65536 if case == 31 else 80
    storage = t.alloc((particle_count + 2) * 16, "positions",
                      fill="zero" if case == 31 else "random")
    points = storage + 16
    strength = rng.choice((0.0, -0.0, 0.25, 1.0, -0.5, 1.5, rng.uniform(-2, 2)))
    if case == 25:
        strength = rng.choice((f32(1), f32(0x807FFFFF)))
    if case == 26:
        strength = rng.choice((float("nan"), float("inf"), -float("inf")))

    pairs = []
    for i in range(padded):
        a, b = rng.sample(range(80), 2)
        if case == 1:
            a, b = 2 * i, 2 * i + 1  # independent pairs
        elif case == 2:
            a, b = i % 3, (i + 1) % 3  # overlap within and across batches
        elif case == 3:
            a = b = i % 5
        elif case == 4:
            a, b = 1, 2  # later duplicate records must overwrite earlier ones
        elif case == 5:
            a, b = (1, 2) if i % 2 == 0 else (2, 1)
        elif case == 31:
            a, b = 65535 - i, 32768 + i
        pairs.append((a, b))
    for index in {index for pair in pairs for index in pair}:
        vector(t, points + index * 16, [rng.uniform(-10, 10) for _ in range(4)])

    for i, (a, b) in enumerate(pairs):
        first = [3.0, 4.0, 0.0, rng.uniform(-100, 100)]
        second = [0.0, 0.0, 0.0, rng.uniform(-100, 100)]
        rest = rng.uniform(0.01, 300)
        weight = rng.choice((0.0, 1.0, 0.5, -0.5, 1.5, rng.uniform(-1, 2)))
        compression = rng.choice((0.0, 1.0, -0.5, 0.25, 2.0, rng.uniform(-2, 2)))
        if 6 <= case <= 14:
            rest = (0.0, 16.0, 25.0, 36.0, f32(0x41C7FFFF),
                    f32(0x41C80001), -1.0, -25.0, -0.0)[case - 6]
        elif case == 15:
            first = second = [0.0, -0.0, 0.0, 7.0]
            rest = 0.0
        elif case == 16:
            first = second = [2.0, 3.0, 4.0, -0.0]
            rest = 1.0
        elif case == 17:
            first[3] = float("nan")  # w must not contaminate the xyz distance
        elif case == 18:
            first[0] = float("nan")
        elif case == 19:
            second[1] = rng.choice((float("inf"), -float("inf")))
        elif case == 20:
            rest = rng.choice((float("nan"), float("inf"), -float("inf")))
        elif case == 21:
            weight = rng.choice((float("nan"), float("inf"), -float("inf")))
        elif case == 22:
            compression = float("nan")
            rest = 36.0  # force the compression branch to select NaN
        elif case == 23:
            first = [f32(1), f32(0x807FFFFF), -0.0, 0.0]
            rest = f32(1)
        elif case == 24:
            first, second = [f32(0x00800001), 0.0, 0.0, 1.0], [f32(0x00800000), 0.0, 0.0, 2.0]
            rest = 1.0  # subtraction result flushes to zero
        elif case == 27:
            first = [f32(0x1A000000), 0.0, 0.0, 3.0]
            rest = 0.0  # squared distance underflows in dot3
        elif case == 28:
            weight = rng.choice((f32(1), f32(0x807FFFFF)))
        elif case == 29:
            first[0] = f32(0x7F7FFFFF)  # distance overflow
        if case >= 6:
            vector(t, points + a * 16, first)
            vector(t, points + b * 16, second)
        record = records + i * 16
        t.w16(record, a)
        t.w16(record + 2, b)
        t.wf32(record + 4, rest)
        t.wf32(record + 8, weight)
        t.wf32(record + 12, compression)
        t.ignore(points + a * 16 + 12, 4)
        t.ignore(points + b * 16 + 12, 4)

    # lvx/stvx round the position base down, including low pointer bits.
    position_arg = points + (rng.randrange(16) if case == 30 else 0)
    if case == 0:
        position_arg = 0
        records = 0
    # A C++ float argument arrives already rounded; the checker also accepts
    # arbitrary doubles in FPRs, which would violate that caller contract.
    strength = struct.unpack(">f", struct.pack(">f", strength))[0]
    t.args(r3=count, r4=position_arg, r5=records, f1=strength)
