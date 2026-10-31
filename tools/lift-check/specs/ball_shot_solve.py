"""0x822851D0: full angle sampling and selection, including both signed-index
sets, the backwards threshold scan, no-sample fallback, and special swing types.

The trajectory and sampler are independently scripted boundaries. The trajectory
has stack arguments: decode their Xenon/SysV caller locations explicitly and
copy them to compared memory, along with the angle and sampled range metadata.
"""
import math
import struct
from liftcheck.spec import *

FUNCTION = "BallShot_Solve"
ADDRESS = 0x822851D0
SOURCE = "src/game/ball/ball_shot_solve.cpp"
TRIALS = 1200
FP_CONTRACT = "off"
SCRIPT = [0]
PROBE = [0]


def _u32(ctx, addr):
    return struct.unpack(">I", ctx.read(addr, 4))[0]


def _trajectory(ctx):
    script = SCRIPT[0]
    probe = PROBE[0]
    sp = ctx.m.gpr(1)
    flag_off, ptr_off = (0x57, 0x64) if ctx.side == "orig" else (11, 12)
    flag = ctx.read(sp + flag_off, 1)[0]
    ptr = _u32(ctx, sp + ptr_off)
    ctx.write(probe, struct.pack(">IIff", flag, ptr, ctx.f(1), ctx.f(2)))
    ctx.write(probe + 16, ctx.read(0x82606580, 4))
    ctx.write(ctx.r(9), ctx.read(script + 16, 16))
    # Simulate the solver publishing new ball/table state; later height/width
    # accesses must reload those globals rather than cache the earlier values.
    table, ball_slot = struct.unpack(">II", ctx.read(script + 32, 8))
    ctx.write(0x8271A304, struct.pack(">I", table))
    ctx.write(0x8271A2F4, struct.pack(">I", ball_slot))
    ctx.write(0x82606580, struct.pack(">I", 37))
    ctx.ret(r3=_u32(ctx, script + 12))


def _sample(ctx):
    script, probe = SCRIPT[0], PROBE[0]
    batch = ctx.r(8)
    ordinal = _u32(ctx, script)
    ctx.write(script, struct.pack(">I", ordinal + 1))
    ctx.write(probe + 32 + ordinal * 12, ctx.read(batch + 0x800, 12))
    ctx.write(batch + 0x80C, ctx.read(script + 4 + ordinal * 4, 4))
    samples = script + 64 + ordinal * 0x800
    ctx.write(batch, ctx.read(samples, 0x800))
    ctx.ret()


def _acos(ctx):
    x = ctx.f(1)
    ctx.ret(f1=math.acos(x) if -1.0 <= x <= 1.0 else math.nan)


CALLS = {
    "BallShot_SolveTrajectory": model(_trajectory,
        args=("r3", "r4", "r5", "r7", "r8", "r9", "r10", "f1", "f2"),
        deref={"r4": 16, "r5": 16}),
    "BallShot_SampleAngles": model(_sample,
        args=("r3", "r4", "r5", "r7", "r8", "r9", "f1"),
        deref={"r4": 16, "r5": 16}),
    "crt_acos": model(_acos),
}


def inputs(t):
    rng = t.rng
    entry = t.alloc(0x1A0, "shot entry", floats=[(0x50, 4), (0x90, 4), (0x178, 2)])
    spin = t.alloc(16, "spin", floats=[(0, 4)])
    velocity = t.alloc(16, "output velocity", floats=[(0, 4)])
    start = t.alloc(16, "start", floats=[(0, 4)])
    target = t.alloc(16, "target", floats=[(0, 4)])
    for p in (spin, start, target, entry + 0x50, entry + 0x90):
        t.floats(p, 4, -5, 5)
    # Ensure both branches of the all-lane comparison are exercised.
    if t.index % 5 == 0:
        for lane in range(3):
            t.wf32(entry + 0x50 + lane * 4, -1)
            t.wf32(entry + 0x90 + lane * 4, 1)
    swing = [6, 11, 3, 7, 9, 10][t.index % 6]
    t.w32(entry + 0xCC, swing)
    t.wf32(entry + 0x178, rng.uniform(0.4, 1.5))
    # Deliberately differs from the selected active player's index.
    t.w32(entry + 0x60, rng.randrange(-31, 32))

    script = t.alloc(64 + 0x1000, "script", fill="zero")
    SCRIPT[0] = script
    probe = t.alloc(64, "probe", fill="zero", floats=[(8, 2), (32, 6)])
    PROBE[0] = probe
    t.w32(script + 4, [0, 1, 32, -1, 32, 32, 32][t.index % 7])
    t.w32(script + 8, rng.choice([0, 1, 32]))  # not the gate used for either sign
    t.w32(script + 12, rng.choice([0, 1, 7]))  # initial solver result is ignored
    for lane in range(4):
        t.wf32(script + 16 + lane * 4, rng.uniform(-20, 20))
    if t.index % 19 == 0:
        for lane in range(4): t.wf32(script + 16 + lane * 4, 0)
    for side in range(2):
        for sample in range(32):
            p = script + 64 + side * 0x800 + sample * 0x40
            t.floats(p, 4, -100, 100)
            t.wf32(p + 0x30, rng.choice([0.1, 0.7, 1.4, rng.uniform(0, 1.7)]))

    tables, slots = [], []
    for n in range(2):
        table = t.alloc(0x20, f"table {n}", floats=[(0x14, 2)])
        t.wf32(table + 0x14, rng.uniform(0.3, 1.0))
        t.wf32(table + 0x18, rng.uniform(0.4, 2.0))
        tables.append(table)
        slot = t.alloc(4, f"ball slot {n}")
        inst = t.alloc(8, f"ball {n}")
        arch = t.alloc(0x10, f"archetype {n}")
        bound = t.alloc(12, f"bound {n}", floats=[8])
        t.wf32(bound + 8, rng.uniform(0.01, 0.15))
        t.w32(arch + 12, bound)
        t.w32(inst + 4, arch)
        t.w32(slot, rng.choice([0, inst, inst]))
        slots.append(slot)
    t.w32(0x8271A304, tables[0])
    t.w32(0x8271A2F4, slots[0])
    t.w32(script + 32, tables[1])
    t.w32(script + 36, slots[1])

    inp = t.alloc(0x90, "input", floats=[(0x84, 2)])
    t.wf32(inp + 0x84, rng.uniform(0.05, 0.5))
    t.wf32(inp + 0x88, rng.uniform(0.05, 0.5))
    t.w32(0x825EAB28, inp)
    slot = rng.randrange(2)
    t.w32(0x82606578, slot)
    index = [0, 1, 2, 3, 4, 15, 30, 31, -1, -2, -15, -31][(t.index // 6) % 12]
    t.w32(0x8261A3D0 + slot * 0x1A0 + 0x60, index)
    t.w32(0x82606580, rng.getrandbits(32))
    for lane in range(4):
        t.w32(0x82619BE0 + lane * 4, 0xffffffff if lane < 3 else 0)
        t.w32(0x82619BD0 + lane * 4, 0x3f800000 if lane == 3 else 0)
        t.wf32(0x82619BF0 + lane * 4, rng.choice([0.0, float("inf")]))
        t.wf32(0x82606750 + lane * 4, 0)
    t.args(r3=entry, r4=start, r5=target, r6=spin, r7=velocity, f1=rng.uniform(1, 30))
