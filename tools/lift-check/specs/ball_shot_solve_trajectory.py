"""0x822860D8: full Newton/backtracking solver and contact-based retries.

The flight simulator is a modeled original boundary; cases include convergent
linear endpoints, singular derivatives, no improvement, the 64-iteration cap,
sample/report paths, target repair, recursive retries and the 128-call guard.
Both ABI layouts of the root's two stack arguments are initialized explicitly.
The original finite-difference temp leaves w uninitialized until its optional
geometry setup runs: zero-fill the stack for that padding lane; computed and
target-provided w values are still compared at every simulator call.
"""
import math
import struct
from liftcheck.spec import *
from liftcheck.machine import STACK_TOP

FUNCTION = "BallShot_SolveTrajectory"
ADDRESS = 0x822860D8
SOURCE = "src/game/ball/ball_shot_trajectory.cpp"
TRIALS = 1000
FP_CONTRACT = "off"
SCRIPT = [0]
PROBE = [0]


def _u32(ctx, addr): return struct.unpack(">I", ctx.read(addr, 4))[0]
def _f32(value): return struct.unpack(">f", struct.pack(">f", value))[0]
def _vec(ctx, addr): return struct.unpack(">4f", ctx.read(addr, 16))


def _simulate(ctx):
    script, probe = SCRIPT[0], PROBE[0]
    mode, calls, bases, initial_depth = struct.unpack(">4I", ctx.read(script, 16))
    sp = ctx.m.gpr(1)
    contacts = _u32(ctx, sp + (0x54 if ctx.side == "orig" else 8))
    base = contacts != 0
    flags_in = ctx.read(contacts + 0x28, 3) if base else b"\0\0\0"
    ctx.write(probe + (calls % 1024) * 4, bytes([int(base)]) + flags_in)
    ctx.write(script + 4, struct.pack(">I", calls + 1))
    start, velocity, target = (_vec(ctx, ctx.r(n)) for n in (4, 5, 7))
    if base:
        bases += 1
        ctx.write(script + 8, struct.pack(">I", bases))
        ctx.write(script + 64, ctx.read(ctx.r(5), 16))
    if mode == 0:
        result = target
    elif mode == 1:
        result = (start[0] + velocity[0], target[1], start[2] + velocity[2], 0)
    elif mode == 2:
        result = (target[0] + .75, target[1], target[2] - .5, 0)
    else:
        # Base errors drive the solver's iteration/line-search policies; probe
        # calls retain a smooth local derivative around that base velocity.
        if base:
            error = 1.0 / bases if mode == 3 else (1.0 if mode == 4 else 1.0 / ((bases + 4) // 5))
            result = (target[0] + error, target[1], target[2] - error * .5, 0)
            ctx.write(script + 80, struct.pack(">4f", *result))
        else:
            base_velocity = _vec(ctx, script + 64)
            base_result = _vec(ctx, script + 80)
            result = (base_result[0] + (velocity[0] - base_velocity[0]), target[1],
                      base_result[2] + (velocity[2] - base_velocity[2]), 0)
    ctx.write(ctx.r(9), struct.pack(">4f", *result))
    if base:
        data = bytearray(ctx.read(script + 96, 0x2C))
        depth = _u32(ctx, 0x82606580)
        # A retry gets a valid non-obstructed report so recursive cases finish.
        if depth > initial_depth + 1:
            data[0x28:0x2B] = bytes([ctx.r(8) & 0xff, 0, 0])
        ctx.write(contacts, data)
    ctx.ret()


def _cos_sin(ctx):
    ctx.write(ctx.r(3), struct.pack(">f", math.cos(ctx.f(1))))
    ctx.write(ctx.r(4), struct.pack(">f", math.sin(ctx.f(1))))
    ctx.ret()


def _asin(ctx):
    x = ctx.f(1)
    ctx.ret(f1=math.asin(x) if -1 <= x <= 1 else math.nan)


CALLS = {
    "BallShot_SimulateTrajectory": model(_simulate,
        args=tuple(f"r{n}" for n in range(3, 11)),
        deref={"r4": 16, "r5": 16, "r6": 16, "r7": 16}),
    "crt_sqrt": model(lambda ctx: ctx.ret(f1=math.sqrt(ctx.f(1)))),
    "crt_sin": model(lambda ctx: ctx.ret(f1=math.sin(ctx.f(1)))),
    "crt_cos": model(lambda ctx: ctx.ret(f1=math.cos(ctx.f(1)))),
    "crt_asin": model(_asin),
    "ph_Atan2fSafe": model(lambda ctx: ctx.ret(f1=_f32(math.atan2(ctx.f(1), ctx.f(2))))),
    "rage::cosSin": model(_cos_sin),
    "nop_8240E6D0": stub(ret="void", args=("r3",)),
}


def inputs(t):
    rng = t.rng
    if not getattr(rng, "_trajectory_zero_stack", False):
        old = rng.randbytes
        rng.randbytes = lambda n: bytes(n) if n == 0x9000 else old(n)
        rng._trajectory_zero_stack = True
    entry = t.alloc(0x1A0, "entry", floats=[0x178])
    t.wf32(entry + 0x178, rng.choice([.5, 1.0, 1.5]))
    start = t.alloc(16, "start", floats=[(0, 4)])
    target = t.alloc(16, "target", floats=[(0, 4)])
    spin = t.alloc(16, "spin", floats=[(0, 4)])
    velocity = t.alloc(16, "velocity", floats=[(0, 4)])
    for p in (start, target, spin, velocity): t.floats(p, 4, -2, 2)
    t.wf32(start + 8, rng.choice([-2, -1, -0.0, 0.0, 1, 2]))
    t.wf32(target + 8, rng.choice([-1.5, -.5, 0, .5, 1.5]))
    t.wf32(start + 12, rng.choice([0, 1, -1]))
    t.wf32(target + 12, rng.choice([0, 1, -1]))
    sample = t.alloc(0x40, "sample", floats=[(0, 10), 0x30])
    sample_arg = sample if rng.randrange(3) else 0
    if sample_arg and rng.randrange(2): velocity = sample
    first = rng.choice([0, 1, 0x100, 0x101, 0xff])
    second = rng.choice([0, 1, 0x100, 0x101])
    stack_flag = rng.randrange(2)
    speed, angle = _f32(rng.uniform(2, 12)), _f32(rng.choice([-.4, -.1, 0, .3, 1.4]))
    depth = rng.choice([0, 0, 0, 0, 126, 127, 128])
    t.w32(0x82606580, depth)
    t.stack_patches[STACK_TOP + 0x57] = bytes([stack_flag])
    t.stack_patches[STACK_TOP + 0x64] = struct.pack(">I", sample_arg)
    t.stack_patches[STACK_TOP + 11] = bytes([stack_flag])
    t.stack_patches[STACK_TOP + 12] = struct.pack(">I", sample_arg)

    table = t.alloc(0x20, "table", floats=[(0x10, 3)])
    t.wf32(table + 0x10, rng.uniform(1, 3))
    t.wf32(table + 0x14, rng.uniform(.4, 1))
    t.wf32(table + 0x18, rng.uniform(1.5, 4))
    t.w32(0x8271A304, table)
    slot = t.alloc(4, "ball slot")
    inst = t.alloc(8, "ball")
    arch = t.alloc(16, "archetype")
    bound = t.alloc(12, "bound", floats=[8])
    t.wf32(bound + 8, rng.uniform(.01, .1))
    t.w32(arch + 12, bound)
    t.w32(inst + 4, arch)
    t.w32(slot, rng.choice([0, inst, inst]))
    t.w32(0x8271A2F4, slot)
    t.wf32(0x826064B8, rng.uniform(-.1, .1))
    t.wf32(0x825C8A50, 10)
    t.wf32(0x825C8078, rng.uniform(.005, .03))
    t.wf32(0x825C8084, .2)
    for lane in range(4):
        t.wf32(0x82619BF0 + lane * 4, float("inf"))
        t.wf32(0x82606750 + lane * 4, 0)
    script = t.alloc(160, "script", fill="zero", floats=[(64, 16)])
    SCRIPT[0] = script
    PROBE[0] = t.alloc(4096, "contact-argument probe", fill="zero")
    t.w32(script, t.index % 6)
    t.w32(script + 12, depth)
    for off in (96, 112): t.floats(script + off, 4, -4, 4)
    t.wf32(script + 128, rng.uniform(.1, 2))
    t.wf32(script + 132, rng.uniform(.1, 2))
    flags = [(1, 0, 0), (0, 0, 0), (1, 1, 0), (1, 0, 1), (0, 0, 1), (0, 1, 1)][(t.index // 6) % 6]
    for off, value in enumerate(flags): t.w8(script + 136 + off, value)
    t.args(r3=entry, r4=start, r5=target, r6=rng.getrandbits(32), r7=spin, r8=first,
           r9=velocity, r10=second, f1=speed, f2=angle)
