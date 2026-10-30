"""0x82337008: position update and mode-1 surface-motion correction.

The original takes v1/v2/v3; the portable lift takes references in r6/r7/r8.
Populate both with the same float32 values. No original instructions are patched.
"""
import math

from liftcheck.spec import *  # noqa: F401,F403

FUNCTION = "lvlTable_7008_2h"
ADDRESS = 0x82337008
SOURCE = "src/game/match/lvl_table.cpp"
FP_CONTRACT = "off"
# The emulator supplies true reciprocals/rsqrts for the VMX estimates. Keep the
# refinement steps in the lift, with a small tolerance for scalar sqrt/divide.
# This also treats NaNs numerically: scalar/VMX NaN sign bits can differ.
FTOL = 1e-6
TRIALS = 2000


def vector(t, name, values):
    addr = t.alloc(16, name)
    for i, value in enumerate(values):
        t.wf32(addr + 4 * i, value)
    return addr


def inputs(t):
    rng = t.rng
    case = rng.randrange(12)
    self = t.alloc(0x170, "motion", ctype="LvlTableMotionView")
    transforms = t.alloc(4 * 64, "transforms")
    indices = t.alloc(5 * 4, "transformIndices")
    for i in range(5):
        t.w32(indices + i * 4, rng.randrange(4))
    t.w32(self + 0x140, transforms)
    t.w32(self + 0x148, indices)
    t.w32(self + 0x150, rng.randrange(5))
    for m in range(4):
        for row in range(4):
            for col in range(4):
                value = float(row == col) if case in (0, 1, 2) else rng.uniform(-2, 2)
                t.wf32(transforms + m * 64 + row * 16 + col * 4, value)
    t.floats(self + 0x50, 8, -2, 2)
    t.floats(self + 0x70, 4, 0, 10)
    t.floats(self + 0x160, 4, -5, 5)

    position = [rng.uniform(-10, 10) for _ in range(4)]
    direction = [rng.uniform(-1, 1) for _ in range(3)] + [0.0]
    length = math.sqrt(sum(x * x for x in direction[:3]))
    direction = [x / length for x in direction]
    step = [rng.uniform(0, 2)] * 4
    origin = [rng.uniform(-10, 10) for _ in range(4)]
    if case in (0, 1, 2):
        # Exact zero tangent, a tangent at the strict threshold, and both signs
        # of normal motion; identity transforms make the boundary reproducible.
        direction = [1.0, 0.0, 0.0, 0.0]
        position = [0.0, 0.0, 0.0, 7.0]
        step = [0.0] * 4
        origin = [0.0] * 4
        for i, value in enumerate([rng.choice([-1.0, 0.0, 1.0]), float(case), 0.0, 0.0]):
            t.wf32(self + 0x160 + i * 4, value)
        for i in range(4):
            t.wf32(self + 0x70 + i * 4, float(case * case))
    elif case == 3:
        # Exercise all four vector lanes and non-unit directions, too.
        direction = [rng.uniform(-3, 3) for _ in range(4)]
        step = [rng.uniform(-2, 2) for _ in range(4)]
    elif case == 4:
        # A zero w result makes the final vnmsub's sign-of-zero observable.
        position[3] = 0.0

    pos = vector(t, "position", position)
    # The w lane does not need estimate tolerance. Compare its bits, including
    # signed zero; this also exposes the otherwise easily missed merge lane.
    t.float_words.discard(pos + 12)
    d = vector(t, "direction", direction)
    s = vector(t, "step", step)
    o = vector(t, "origin", origin)
    # High mode bits are ignored; include mode 0/2/ffff and high-word-only 1.
    mode = rng.choice([1, 1, 1, 0xABCD0001, 0, 2, 0xFFFF, 0x10000])
    if case in (0, 1, 2, 3):
        mode = 1
    if (mode & 0xFFFF) != 1:
        # The fast path must not even read self.
        self = 0
    t.args(r3=self, r4=pos + rng.randrange(16), r5=mode,
           r6=d, r7=s, r8=o, v1=direction, v2=step, v3=origin)
