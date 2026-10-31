"""Full increasing/decreasing sample loops, 32-sample cap, dynamic bounds and
speed limits, four-lane normalization/clamp, and explicit helper stack args."""
import struct
from liftcheck.spec import *

FUNCTION = "BallShot_SampleAngles"
ADDRESS = 0x82285A70
SOURCE = "src/game/ball/ball_shot_trajectory.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
SCRIPT = [0]
PROBE = [0]


def _u32(ctx, addr):
    return struct.unpack(">I", ctx.read(addr, 4))[0]


def _solve(ctx):
    script, probe = SCRIPT[0], PROBE[0]
    batch, ordinal, mode = struct.unpack(">III", ctx.read(script, 12))
    sp = ctx.m.gpr(1)
    byte_off, ptr_off = (0x57, 0x64) if ctx.side == "orig" else (11, 12)
    # Compare both extra arguments, not merely the register arguments.
    ctx.write(probe + ordinal * 12, bytes(ctx.read(sp + byte_off, 1)) + b"\0\0\0"
              + ctx.read(sp + ptr_off, 4) + ctx.read(0x82606580, 4))
    ctx.write(script + 4, struct.pack(">I", ordinal + 1))
    ctx.write(0x82606580, struct.pack(">I", ordinal + 17))
    vector = struct.unpack(">4f", ctx.read(script + 16, 16))
    if mode & 1:
        vector = tuple(x * (1 + ordinal * .1) for x in vector)
    ctx.write(ctx.r(9), struct.pack(">4f", *vector))
    ctx.write(ctx.r(3) + 0xB0, ctx.read(script + 32, 4))
    if ordinal == 0 and mode & 2:
        ctx.write(batch + 0x808, ctx.read(script + 36, 4))
    if ordinal == 0 and mode & 4:
        ctx.write(batch + 0x800, ctx.read(script + 40, 8))
    ctx.ret(r3=ctx.rng.choice([0, 1, 7]))


CALLS = {
    "BallShot_SolveTrajectory": model(_solve,
        args=("r3", "r4", "r5", "r7", "r8", "r9", "r10", "f1", "f2"),
        deref={"r4": 16, "r5": 16}),
}


def inputs(t):
    rng = t.rng
    entry = t.alloc(0x1A0, "entry", floats=[0xB0])
    start = t.alloc(16, "start", floats=[(0, 4)])
    target = t.alloc(16, "target", floats=[(0, 4)])
    spin = t.alloc(16, "spin", floats=[(0, 4)])
    for p in (start, target, spin): t.floats(p, 4, -10, 10)
    t.wf32(entry + 0xB0, rng.uniform(1, 10))
    batch = t.alloc(0x810, "sample set", floats=[(0x800, 3)])
    for n in range(32):
        for off in (0, 4, 8, 12, 0x30):
            t.wf32(batch + n * 0x40 + off, rng.uniform(-10, 10))
    ranges = [(0, 1, .1), (1, 1, .1), (2, 1, .1), (0, 1, 0),
              (0, 1, -.01), (-1, 1, .001), (0, 1, float("nan")),
              (float("nan"), 1, .1), (0, float("nan"), .1)]
    low, high, step = ranges[t.index % len(ranges)]
    t.wf32(batch + 0x800, low)
    t.wf32(batch + 0x804, high)
    t.wf32(batch + 0x808, step)
    script = t.alloc(64, "script", fill="zero", floats=[(16, 8)])
    SCRIPT[0] = script
    PROBE[0] = t.alloc(32 * 12, "stack-argument probe", fill="zero")
    for off, value in [(0, batch), (4, 0), (8, rng.randrange(8))]: t.w32(script + off, value)
    values = [0, 1, -1, rng.uniform(-20, 20), 1e-40, -1e-40]
    for lane in range(4): t.wf32(script + 16 + lane * 4, rng.choice(values))
    t.wf32(script + 32, rng.choice([0, -1, 1, 5, 50, float("nan")]))
    t.wf32(script + 36, rng.choice([.05, .5, 2, 0, -.1]))
    t.wf32(script + 40, rng.uniform(-2, 0))
    t.wf32(script + 44, rng.uniform(0, 2))
    t.w32(0x82606580, rng.getrandbits(32))
    for lane in range(4):
        t.wf32(0x82619BF0 + lane * 4, float("inf"))
        t.wf32(0x82606750 + lane * 4, 0)
    t.args(r3=entry, r4=start, r5=target, r6=rng.getrandbits(32), r7=spin, r8=batch,
           r9=rng.choice([0, 1, 0x100, 0x101, -1, -256]), f1=rng.uniform(1, 25))
