"""0x823D85B8: indexed cloth rest-length constraint, with per-lane response.

Mirror v1 in the portable entry's r6 reference. No patched instructions, ignored
memory, or stubbed callees. Cover strict rest-length and response-clamp boundaries,
nonuniform lanes, zero lengths, NaNs/infinities, signed zero, VMX DAZ/FTZ, wrapped
indices, misaligned vector bases, and input/output aliasing.

Limits: lift-check supplies exact rsqrt rather than Xenon's estimate, and models
VMX multiply-adds with separately rounded products. The lift follows CODING_STYLE's
explicit fused vmaddfp rule; FTOL allows the resulting small numeric differences
and their amplification by cancellation in the final position subtraction.
NaNs compare numerically, without payload/sign guarantees. vmsum3fp128 follows the
emulator's double-accumulation model, not verified Xenon intermediate precision.
Adversarial cancellation at the response clamp is not established by this check.
"""
import struct

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "lvlTable_85B8_2hr"
ADDRESS = 0x823D85B8
SOURCE = "src/game/match/lvl_table.cpp"
FP_CONTRACT = "off"
FTOL = 1e-5
TRIALS = 2000


def f32(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def vector(t, address, values):
    for lane, value in enumerate(values):
        t.wf32(address + lane * 4, value)


def inputs(t):
    rng = t.rng
    case = rng.randrange(32)
    self = t.alloc(0x3C, "constraint", ctype="LvlTableConstraintView")
    indices = t.alloc(8 * 4, "particleIndices")
    positions = t.alloc(8 * 16, "positions")
    rest = t.alloc(8 * 16, "restLength")
    base = t.alloc(8 * 16, "responseBase")
    scale = t.alloc(8 * 16, "responseScale")
    anchor = t.alloc(16, "anchor")
    slot, particle = rng.randrange(8), rng.randrange(8)
    for i in range(8):
        t.w32(indices + i * 4, rng.randrange(8))
        vector(t, positions + i * 16, [rng.uniform(-10, 10) for _ in range(4)])
        vector(t, rest + i * 16, [rng.uniform(0, 10) for _ in range(4)])
        vector(t, base + i * 16, [rng.uniform(-1, 2) for _ in range(4)])
        vector(t, scale + i * 16, [rng.uniform(-2, 2) for _ in range(4)])
    t.w32(indices + slot * 4, particle | (rng.randrange(16) << 28))
    point = [rng.uniform(-10, 10) for _ in range(4)]
    origin = [rng.uniform(-10, 10) for _ in range(4)]
    length = [rng.uniform(0, 10) for _ in range(4)]
    response = [rng.uniform(-1, 2) for _ in range(4)]
    response_scale = [rng.uniform(-2, 2) for _ in range(4)]
    if case < 12:
        # Exactly representable 3-4-5 length: just below, on, and above rest.
        point, origin = [3.0, 4.0, 0.0, 7.0], [0.0] * 4
        length = [[6.0] * 4, [5.0] * 4, [4.0] * 4,
                  [4.0, 5.0, 6.0, 2.0]][case % 4]
        response = [[0.0] * 4, [1.0] * 4, [2.0] * 4,
                    [-0.5, 0.5, 1.5, -1.0]][case // 4]
        response_scale = [0.0] * 4
    elif case == 12:
        point = origin = [0.0, -0.0, 0.0, -0.0]
        length = [0.0] * 4  # both rsqrt singularities
    elif case == 13:
        point = origin = [2.0, 3.0, 4.0, 5.0]
        length = [1.0, 0.0, -1.0, 2.0]
    elif case == 14:
        point[3] = float("nan")  # dot3 excludes w, arithmetic still processes it
    elif case == 15:
        origin[3] = float("inf")
    elif case == 16:
        point[0] = float("nan")
    elif case == 17:
        point[1] = float("inf")
    elif case == 18:
        length = [float("nan"), float("inf"), -float("inf"), -0.0]
    elif case == 19:
        response = [float("nan"), float("inf"), -float("inf"), -0.0]
    elif case == 20:
        response_scale = [float("nan"), float("inf"), -float("inf"), 0.0]
    elif case == 21:
        point = [f32(1), f32(0x807FFFFF), -0.0, f32(0x007FFFFF)]
        origin = [0.0] * 4
        length = [f32(1)] * 4
    elif case == 22:
        point = [f32(0x00800001), 0.0, 0.0, 0.0]
        origin = [f32(0x00800000), 0.0, 0.0, 0.0]  # subtraction FTZ
    elif case == 23:
        point, origin = [f32(0x1A000000), 0.0, 0.0, 1.0], [0.0] * 4  # dot FTZ
        length = [0.0] * 4
    elif case == 24:
        point = [f32(0x7F7FFFFF), 1.0, 2.0, 0.0]  # overflow
    elif case == 25:
        # Strict rest-length test one ulp to either side of the boundary.
        point, origin = [1.0, 0.0, 0.0, -0.0], [0.0] * 4
        length = [f32(0x3F7FFFFF), 1.0, f32(0x3F800001), 0.0]
    elif case == 26:
        point, origin, length = [2.0, 0.0, 0.0, 1.0], [0.0] * 4, [1.0] * 4
        response = [f32(0x3F7FFFFF), 1.0, f32(0x3F800001), -0.5]
        response_scale = [0.0] * 4
    elif case == 27:
        response = [f32(1), f32(0x807FFFFF), -0.0, 0.0]
        response_scale = [0.0] * 4
    vector(t, positions + particle * 16, point)
    vector(t, rest + slot * 16, length)
    vector(t, base + slot * 16, response)
    vector(t, scale + slot * 16, response_scale)
    vector(t, anchor, origin)

    if case == 28:
        rest = positions  # all input loads precede the sole vector store
    elif case == 29:
        base = positions
    elif case == 30:
        scale = positions
    elif case == 31:
        origin = point
        anchor = positions + particle * 16
    if case in (0, 4, 8):
        # A selected original lane must preserve its bits exactly (no FTOL).
        for lane in range(4):
            t.float_words.discard(positions + particle * 16 + lane * 4)
    # w always selects the untouched original: xyz mask clears the compared w.
    t.float_words.discard(positions + particle * 16 + 12)
    t.w32(self + 0x0C, indices)
    t.w32(self + 0x30, base + rng.randrange(16))
    t.w32(self + 0x34, rest + rng.randrange(16))
    t.w32(self + 0x38, scale + rng.randrange(16))
    t.args(r3=self, r4=slot | (rng.randrange(4) << 30),
           r5=positions + rng.randrange(16), r6=anchor, v1=origin)
