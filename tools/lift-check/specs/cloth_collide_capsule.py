"""0x82338730: cloth particles against a capsule, formerly lvlTable_8730.

Run both original callees, bridging their VMX inputs from the portable C++
references. Compare every scalar argument, every vector lane at each call, call
order, and all external writes. Only the original compiler's stack probes are
transparent; no patched instructions, ignored memory, or simulated filtering.

Cover padded batches, both endcaps/interior, strict radial/broad boundaries,
first-index suppression, repeated other indices, signed movable thresholds,
mode-1 response, nonuniform lanes, misaligned vector pointers, empty groups,
NaNs/infinities, zero distance, VMX subnormals, and live reduction/origin aliasing.
Limits: VMX estimates are lift-check's exact reciprocal/rsqrt; dot3 follows its
double-accumulation model. FTOL covers estimate/refinement rounding and compares
NaNs numerically, not by payload/sign. This does not establish console estimates
or integration of the documented internal-ABI bridges into a running game.
"""
import math
import struct

from unicorn import UC_HOOK_CODE
from liftcheck.dwarf import arg_registers
from liftcheck.spec import *

FUNCTION = "clothCollideCapsule"
ADDRESS = 0x82338730
SOURCE = "src/game/match/lvl_table.cpp"
FP_CONTRACT = "off"
FTOL = 1e-6
TRIALS = 2000


class VmxCall(run):
    """Execute the original callee; compare its logical vector arguments too."""

    def __init__(self, args, vectors):
        self.args = args
        self.vectors = vectors

    def handle(self, ctx):
        types = dict(arg_registers(ctx.sig))
        for vector, register in self.vectors:
            if ctx.side == "orig":
                data = struct.pack(">4I", *ctx.m.assist.vmx.v[vector])
            else:
                data = ctx.read(ctx.r(register), 16)
                ctx.m.assist.vmx.v[vector] = list(struct.unpack(">4I", data))
            ctx.rec.derefs[f"v{vector}"] = (data, types[f"r{register}"].pointee)
        # run() keeps the callee in Machine.home. Remove that range on return,
        # so repeated calls are intercepted and bridged/compared as well.
        # This only changes checker dispatch; original instructions stay intact.
        machine, target = ctx.m, ctx.rec.target
        if not hasattr(machine, "_cloth_return_hooks"):
            machine._cloth_return_hooks = {}
        key = (target, ctx.rec.lr)
        if key not in machine._cloth_return_hooks:
            def returned(uc, addr, size, user):
                machine.home[:] = [region for region in machine.home if region[0] != target]

            machine._cloth_return_hooks[key] = machine.uc.hook_add(
                UC_HOOK_CODE, returned, begin=ctx.rec.lr, end=ctx.rec.lr)
        return "run"


CALLS = {
    0x82569394: run(transparent=True),  # _RtlCheckStack12, compiler stack probing
    "lvlTable_7D28_2h": VmxCall(("r3", "r4", "r5", "r6"), ((1, 7), (2, 8))),
    "lvlTable_7008_2h": VmxCall(("r3", "r4", "r5"), ((1, 6), (2, 7), (3, 8))),
}


def f32(bits):
    return struct.unpack(">f", struct.pack(">I", bits))[0]


def vector(t, addr, values):
    for lane, value in enumerate(values):
        t.wf32(addr + lane * 4, value)


def inputs(t):
    rng = t.rng
    case = rng.randrange(32)
    count = rng.choice((0, 1, 31, 32, 33, 63, 64, 65, 96))
    if case < 12:
        count = rng.choice((1, 31, 32, 33, 65))
    padded = (count + 31) & ~31
    self = t.alloc(0x170, "cloth", ctype="ClothCapsuleCollisionView")
    bound = t.alloc(0xC0, "capsule", ctype="ClothCapsuleBoundView")
    groups = t.alloc(4 * 8, "groups")
    indices = t.alloc(max(16, padded * 4), "indices")
    positions = t.alloc(16 * 16, "positions")
    previous = t.alloc(16 * 16, "previousPositions")
    reduction = t.alloc(16, "reduction")
    expansion = t.alloc(16, "expansion")
    group = rng.randrange(4)
    t.w32(self + 0x108, groups)
    t.w32(groups + group * 8, indices)
    t.w16(groups + group * 8 + 4, count)
    t.w16(groups + group * 8 + 6, rng.getrandbits(16))
    first_movable = rng.choice((-0x80000000, -1, 0, 1, 7, 15, 16, 0x7FFFFFFF))
    mode = rng.choice((0, 1, 2, 0xFFFF, 0xABCD0001, 0x10000))
    radius = [1.0] * 4
    length = [2.0] * 4
    start = [-1.0, 0.0, 0.0, 0.0]
    axis = [1.0, 0.0, 0.0, 0.0]
    center = [0.0] * 4
    pad = [rng.uniform(0.0, 0.5)] * 4
    shrink = [rng.uniform(-0.2, 0.5)] * 4
    broad_radius = 5.0
    if case in (26, 30, 31):
        # Rotated, translated capsules exercise all dot3 products and rounded
        # multiply/add steps, beyond the exactly representable axis cases.
        start = [rng.uniform(-1, 1) for _ in range(3)] + [rng.uniform(-1, 1)]
        axis = [rng.uniform(-1, 1) for _ in range(3)] + [0.0]
        norm = math.sqrt(sum(x * x for x in axis[:3]))
        axis = [x / norm for x in axis]
        length = [rng.uniform(0.5, 3.0)] * 4
        center = [start[i] + axis[i] * length[i] * 0.5 for i in range(4)]
    if case < 12:
        # Exact clamping/radial boundaries and zero-length normal.
        first_movable, mode = 0, 0
        pad, shrink = [0.0] * 4, [0.0] * 4
    elif case == 12:
        radius = [1.5, 1.0, 2.0, 3.0]
        length = [0.5, 1.0, 1.5, 2.0]
        axis = [0.5, -0.25, 0.75, -0.5]  # all lanes, no unit-axis assumption
        pad = [0.1, 0.3, 0.2, 0.4]
        shrink = [-0.5, 0.0, 0.5, 1.0]
    elif case == 13:
        pad[2] = float("nan")
    elif case == 14:
        radius[1] = float("nan")
    elif case == 15:
        axis[2] = float("nan")
    elif case == 16:
        length = [float("nan"), float("inf"), -float("inf"), -0.0]
    elif case == 17:
        shrink = [float("nan"), float("inf"), -float("inf"), -0.0]
        first_movable = 0
    elif case == 18:
        pad = [float("inf")] * 4
    elif case == 19:
        # DAZ before the broad-radius add; no scalar FPU FTZ assumption.
        broad_radius, pad = f32(1), [f32(0x807FFFFF)] * 4
    elif case == 20:
        # Amplify a subnormal axis lane into an ordinary-sized closest-point
        # error if DAZ is omitted. Broad filtering still sees small positions.
        axis = [1.0, f32(0x007FFFFF), 0.0, -0.0]
        start, length = [-1.0e38, 0.0, 0.0, 0.0], [1.0e38] * 4
        radius, pad, shrink = [2.0] * 4, [0.0] * 4, [0.0] * 4
        first_movable, mode = 0, 0
    elif case == 21:
        radius, pad = [f32(0x00800001)] * 4, [-f32(0x00800000)] * 4
    elif case == 22:
        radius = [float("inf")] * 4
        first_movable = 0
    elif case == 23:
        broad_radius = float("nan")
    elif case == 24:
        # Strict broad boundary: xyz distance exactly 25.
        pad, radius = [0.0] * 4, [10.0] * 4
    elif case == 25:
        # Strict radius uses all four lanes, including the w radius.
        radius = [10.0, 10.0, 10.0, 0.0]
        pad = [0.0] * 4
    elif case == 26:
        first_movable, mode = 0, 1

    for i in range(16):
        point = [rng.uniform(-3.0, 3.0) for _ in range(3)] + [rng.uniform(-2.0, 2.0)]
        if case < 12:
            point = [(-2.0, -1.0, 0.0, 1.0, 2.0)[i % 5],
                     (0.0, 0.5, 1.0, f32(0x3F7FFFFF), f32(0x3F800001))[case % 5],
                     0.0, float(i % 3)]
            if case == 5:
                point = [0.0, 0.0, 0.0, -0.0]
            elif case == 6:
                point[1] = f32(0x1A000000)  # squared distance FTZ
            elif case == 7:
                point[1] = f32(1)
            elif case == 8:
                point[3] = float("nan")  # ignored by dot3, retained in delta
            elif case == 9:
                point[0] = f32(0x00800001)
                start[0] = f32(0x00800000)
            elif case == 10:
                point = [rng.choice((-2.0, 2.0)), 0.0, 0.0, 0.0]
            elif case == 11:
                point = [0.0, rng.choice((0.25, 0.75, 1.25)), 0.0, 0.0]
        elif case == 24:
            point = [3.0, 4.0, 0.0, 9.0]
        elif case == 20:
            point = [0.0, 0.5, 0.0, 0.0]
        elif case == 27:
            point = [float("nan"), 0.0, 0.0, 0.0]
        elif case == 28:
            point = [float("inf"), 0.0, 0.0, 0.0]
        elif case == 29:
            point = [0.0, 0.5, 0.0, 0.0]
            shrink = [0.1] * 4
            first_movable = 0
        vector(t, positions + i * 16, point)
        vector(t, previous + i * 16, [rng.uniform(-2, 2) for _ in range(4)])
    for i in range(padded):
        index = rng.randrange(16)
        if case in (0, 5, 11):
            index = (3, 3, 4, 4, 3, 5, 4, 3)[i % 8]
        if case == 30:
            index |= rng.randrange(16) << 28  # signed test precedes vector-address masking
        t.w32(indices + 4 * i, index)

    t.w32(self + 8, first_movable)
    vector(t, bound + 0x40, center)
    vector(t, bound + 0x70, radius)
    vector(t, bound + 0x80, length)
    vector(t, bound + 0x90, start)
    vector(t, bound + 0xB0, axis)
    t.wf32(bound + 8, broad_radius)
    vector(t, expansion, pad)
    vector(t, reduction, shrink)
    t.floats(self + 0x50, 8, -1, 1)
    t.floats(self + 0x70, 4, 0, 3)
    t.floats(self + 0x160, 4, -1, 1)
    transforms = t.alloc(64, "transform")
    transform_indices = t.alloc(4, "transformIndices")
    t.w32(transform_indices, 0)
    t.w32(self + 0x140, transforms)
    t.w32(self + 0x148, transform_indices)
    t.w32(self + 0x150, 0)
    for row in range(4):
        vector(t, transforms + row * 16, [float(row == col) for col in range(4)])
    if case == 29:
        reduction = positions + 4 * 16  # response changes an input to later iterations
    elif case == 31:
        previous = positions
    position_pointer = positions + rng.randrange(16)
    t.w32(self + 0x1C, position_pointer)
    t.w32(self + 0x24, previous + rng.randrange(16))
    if count == 0:
        # Only the group/count may be read on the early return.
        bound = reduction = expansion = 0
        t.w32(self + 0x1C, 0)
        t.w32(self + 0x24, 0)
        t.w32(groups + group * 8, 0)
    t.args(r3=self, r4=bound, r5=group | (rng.randrange(8) << 29),
           r6=reduction + (rng.randrange(16) if count else 0),
           r7=expansion + (rng.randrange(16) if count else 0), r8=mode)
