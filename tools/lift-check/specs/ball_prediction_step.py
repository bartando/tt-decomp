"""0x82288368: actual acceleration/bounce, scripted swept table/net geometry.

The sweep may publish new player, table, ball and prediction state before the
material lookup. Checks capsule endpoints, normals, material parameters, all
sample lanes, time fractions and the bank-dependent hittability transition.
"""
import math
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(__file__))
from liftcheck.spec import *
from _bp_common import zero_stack_fill

FUNCTION = "BallPredict_StepSample"
ADDRESS = 0x82288368
SOURCE = "src/game/ball/ball_prediction_step.cpp"
TRIALS = 800
FTOL = 1e-5
FP_CONTRACT = "off"


def u32(ctx, a):
    return struct.unpack(">I", ctx.read(a, 4))[0]


def f32(ctx, a):
    return struct.unpack(">f", ctx.read(a, 4))[0]


def put32(ctx, a, value):
    ctx.write(a, struct.pack(">I", value & 0xFFFFFFFF))


def sweep(ctx):
    control = u32(ctx, ctx.r(3) + 0xC)
    ctx.write(ctx.r(8) + 0x20, ctx.read(control + 0x20, 16))
    ctx.write(ctx.r(8) + 0x30, ctx.read(control + 0x30, 4))
    ctx.write(ctx.r(8) + 0x46, ctx.read(control + 0x34, 2))
    # A live geometry callback can replace the state used by the subsequent
    # normal tilt, material query and selected-shot lookup.
    if u32(ctx, control + 4):
        put32(ctx, 0x8271A304, u32(ctx, control + 8))
        put32(ctx, u32(ctx, 0x8271A2F4), u32(ctx, control + 12))
        put32(ctx, 0x82606578, u32(ctx, control + 16))
        put32(ctx, 0x8271A2F8, u32(ctx, control + 20))
    ctx.ret(r3=u32(ctx, control))


def material(ctx):
    bound = ctx.r(3)
    control = u32(ctx, bound + 0xC)
    if u32(ctx, control + 0x38):
        put32(ctx, 0x8271A304, u32(ctx, control + 0x3C))
        put32(ctx, 0x82606578, u32(ctx, control + 0x40))
    ctx.ret(r3=u32(ctx, bound + 0x10))


def gravity(ctx):
    arch = ctx.r(3)
    control = u32(ctx, arch + 0x28)
    if u32(ctx, control + 0x44):
        put32(ctx, u32(ctx, 0x8271A2F4), 0)
    ctx.ret(f1=f32(ctx, arch + 0x24))


def unary(fn):
    def call(ctx):
        try:
            value = fn(ctx.f(1))
        except ValueError:
            value = float("nan")
        ctx.ret(f1=value)
    return model(call, args=("f1",))


CALLS = {
    "BallFlight_Acceleration": run(),
    "BallFlight_Bounce": run(),
    "archetype.vfn_12": model(gravity, args=("r3",)),
    "table bound.vfn_22": model(sweep, args=("r3", "r4", "r5", "r8", "r9", "f1", "f2"),
                                 deref={"r4": 16, "r5": 16, "r8": 0x50}),
    "ball bound.vfn_11": model(material, args=("r3", "r4")),
    "crt_sqrt": unary(math.sqrt),
    "crt_acos": unary(math.acos),
    "crt_cos": unary(math.cos),
    "crt_sin": unary(math.sin),
    0x82432628: unary(math.tan),
    "nop_8240E6D0": stub(ret="void", args=("r3",)),
}


def inputs(t):
    zero_stack_fill(t)
    rng = t.rng
    case = t.index % 20
    control = t.alloc(0x50, "geometry script")
    loop = t.alloc(0x210, "loop")
    t.wf32(loop + 0x208, rng.choice([29.49, 29.5, 59.49, 59.5, 60.0, 120.0]))
    t.w32(0x825EAB30, loop)

    def state(name):
        state = t.alloc(0x30, name)
        for bank in range(2):
            data = t.alloc(0x2800, f"{name} bank {bank}")
            t.w32(state + 0x10 + 4 * bank, data)
            count = 0 if case == 0 else rng.choice([0, 1, 2, 119, 120])
            tail = rng.choice([0, 118, 119])
            t.w32(data + 0x25A4, tail)
            t.w32(data + 0x25A8, count)
            last = data + 0x20 + ((tail + count) % 120) * 0x50
            t.w8(last + 8, rng.choice([0, 0, 1, 255]))
            t.w8(last + 10, rng.choice([0, 1, 17, 255]))
            t.wf32(data + 0x26B0, rng.choice([0.0, -20.0, 7.0, 0.0000001]))
        t.wf32(state + 0x28, rng.uniform(0.005, 0.05))
        return state

    states = [state("initial state"), state("replacement state")]
    t.w32(0x8271A2F8, states[0])

    def table(name):
        table = t.alloc(0x20, name)
        net = t.alloc(0x80, name + " net")
        t.w32(table, net)
        t.wf32(table + 4, rng.uniform(0.1, 1.5))
        t.wf32(table + 0x14, 0.76)
        t.wf32(table + 0x18, 2.74 if case in (7, 8) else rng.choice([2.74, 3.0]))
        t.wf32(net + 0x78, rng.uniform(0.1, 0.8))
        t.wf32(net + 0x7C, rng.uniform(0.1, 0.9))
        return table

    tables = [table("initial table"), table("sweep table"), table("material table")]
    t.w32(0x8271A304, tables[0])

    def ball(name):
        ball = t.alloc(0x10, name)
        arch = t.alloc(0x30, name + " archetype")
        bound = t.alloc(0x20, name + " bound")
        material = t.alloc(0x10, name + " material")
        t.w32(ball + 4, arch)
        t.w32(arch, t.vtable("archetype", 16))
        t.w32(arch + 0xC, bound)
        t.wf32(arch + 0x24, 0.0 if case in (0, 1, 2) else rng.choice([0.2, 1.0]))
        t.w32(arch + 0x28, control)
        t.w32(bound, t.vtable("ball bound", 24))
        t.wf32(bound + 8, 0.02 if case in (7, 8) else rng.choice([0.02, 0.05]))
        t.w32(bound + 0xC, control)
        t.w32(bound + 0x10, material)
        t.wf32(material + 0xC, rng.uniform(0.1, 1.0))
        return ball

    balls = [ball("initial ball"), ball("replacement ball")]
    slot = t.alloc(4, "ball slot")
    t.w32(slot, balls[0])
    t.w32(0x8271A2F4, slot)
    scene = t.alloc(0x50, "scene")
    owner = t.alloc(0x80, "scene owner")
    proxy = t.alloc(0x20, "scene proxy")
    table_inst = t.alloc(0x10, "table instance")
    table_arch = t.alloc(0x10, "table archetype")
    table_bound = t.alloc(0x20, "table bound")
    t.w32(scene + 0x48, owner)
    t.w32(owner + 0x7C, proxy)
    t.w32(proxy + 0x14, table_inst)
    t.w32(table_inst + 4, table_arch)
    t.w32(table_arch + 0xC, table_bound)
    t.w32(table_bound, t.vtable("table bound", 24))
    t.w32(table_bound + 0xC, control)
    t.w32(0x82606564, scene)
    t.w32(0x82606578, rng.randrange(2))
    for n in range(2):
        shot = 0x8261A3D0 + 0x1A0 * n
        t.wf32(shot + 0xBC, rng.choice([0.95, 0.65, 1.0]))
        t.w32(shot + 0xCC, rng.choice([0, 8, 9, 10]))

    t.wf32(0x825C75F0, 0.004)
    t.wf32(0x825C75FC, 0.011)
    t.wf32(0x825C8078, 0.01)
    t.wf32(0x825CBCE0, 0.0)
    t.wf32(0x825CBCE4, -9.8)
    t.wf32(0x825CBCE8, 0.0)
    t.wf32(0x825CBCEC, 0.0)
    t.wf32(0x825C8080, 0.25)
    t.w32(control, [0, 1, 0x100, 0x101, 255][case % 5])
    t.w32(control + 4, rng.choice([0, 1]))
    t.w32(control + 8, tables[1])
    t.w32(control + 12, balls[1])
    t.w32(control + 16, rng.randrange(2))
    t.w32(control + 20, states[1])
    normal = rng.choice([(0.0, 1.0, 0.0, 0.0), (0.6, 0.8, 0.0, 0.2),
                         (0.0, 0.5, 0.8660254, -0.1), (1.0, 0.0, 0.0, 0.0),
                         (0.0, -1.0, 0.0, 0.0)])
    for i, value in enumerate(normal):
        t.wf32(control + 0x20 + 4 * i, value)
    t.wf32(control + 0x30, rng.choice([-0.5, 0.0, 0.2, 0.5, 1.0, 1.5]))
    t.w16(control + 0x34, rng.choice([0, 0, 1, 2]))
    t.w32(control + 0x38, rng.choice([0, 1]))
    t.w32(control + 0x3C, tables[2])
    t.w32(control + 0x40, rng.randrange(2))
    t.w32(control + 0x44, 1 if case == 0 else 0)

    sample = t.alloc(0x50, "sample", floats=[(0, 2), (0x10, 16)])
    t.wf32(sample, rng.uniform(0, 10))
    t.wf32(sample + 4, rng.uniform(0, 10))
    t.w8(sample + 8, rng.choice([0, 1, 255]))
    t.w8(sample + 9, rng.choice([0, 1, 255]))
    t.w8(sample + 10, rng.choice([0, 1, 17, 255]))
    t.floats(sample + 0x10, 16, -3, 3)
    t.wf32(sample + 0x10, rng.uniform(-0.5, 0.5))
    t.wf32(sample + 0x14, rng.choice([0.01, 0.76, 0.78, 1.0, 5.0]))
    t.wf32(sample + 0x18, 5.0 if case == 3 else rng.uniform(-0.5, 0.5))
    if case == 0:
        for off in range(0x20, 0x40, 4):
            t.wf32(sample + off, 0.0)   # zero displacement and zero speed
        t.w32(sample + 0x14, 1)        # flushed onto a zero-radius floor
        t.w8(sample + 10, 17)
    elif case in (1, 2):
        t.wf32(sample + 0x10, 100000000.0)
        t.wf32(sample + 0x14, 100000000.0)
        t.wf32(sample + 0x18, 0.0)
        for off in range(0x20, 0x40, 4):
            t.wf32(sample + off, 0.0)
        t.wf32(sample + 0x20, 0.001 if case == 1 else 0.0000001)
    elif case == 4:
        t.wf32(sample + 0x14, 0.779)
        t.wf32(sample + 0x24, -1.0)
        t.w8(sample + 9, 1)            # previous net contact, descending skim
    elif case == 5:
        t.wf32(sample + 0x30, 100000.0) # z velocity sign reversal
    elif case in (7, 8):
        t.wf32(sample + 0x18, 1.45 if case == 7 else 1.35)
        t.wf32(sample + 0x28, -8.0 if case == 7 else 8.0)
    elif case == 9:
        t.wf32(sample + 0x14, float("nan"))
    elif case == 10:
        t.w32(sample + 0x1C, 1)        # VMX flushes this subnormal position lane
        t.wf32(sample + 0x2C, 0.0)
    t.args(r3=sample, r4=rng.randrange(2))
