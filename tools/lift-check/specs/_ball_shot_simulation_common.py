"""Inputs and real-boundary models shared by candidate-flight simulation specs."""
import struct
from liftcheck.spec import *
from liftcheck.machine import STACK_TOP

SCRIPT = [0]


def _u32(ctx, address): return struct.unpack(">I", ctx.read(address, 4))[0]
def _f32(ctx, address): return struct.unpack(">f", ctx.read(address, 4))[0]
def _vec(ctx, address): return struct.unpack(">4f", ctx.read(address, 16))


def poll(ctx):
    value, mode = struct.unpack(">II", ctx.read(ctx.r(3), 8))
    ctx.write(0x825C9A2C, struct.pack(">I", mode))
    ctx.ret(r3=value)


def acceleration(ctx):
    script = SCRIPT[0]
    calls, bounced = struct.unpack(">II", ctx.read(script, 8))
    ctx.write(script, struct.pack(">I", calls + 1))
    vector = list(_vec(ctx, script + 16))
    if bounced and _u32(ctx, script + 8) == 14: vector[1] = 0
    velocity = _vec(ctx, ctx.r(5))
    drag = _f32(ctx, script + 32)
    vector[0] -= drag * velocity[0]
    vector[2] -= drag * velocity[2]
    ctx.write(ctx.r(3), struct.pack(">4f", *vector))
    # The original caller reloads the acceleration through r3 after this void
    # boundary; the original leaf leaves its output pointer there.
    ctx.ret(r3=ctx.r(3))


def material(ctx):
    script = SCRIPT[0]
    if _u32(ctx, script + 12):
        ctx.write(0x8271A304, ctx.read(script + 36, 4))
        ctx.write(_u32(ctx, script + 44) + 0xBC, ctx.read(script + 48, 4))
    ctx.ret(r3=_u32(ctx, script + 40))


def bounce(ctx):
    script = SCRIPT[0]
    position, velocity, spin = (list(_vec(ctx, ctx.r(n))) for n in (5, 6, 7))
    position[1] += .002
    velocity[1] = abs(velocity[1]) * ctx.f(3)
    friction = ctx.f(2)
    velocity[0] *= 1 - .1 * friction
    velocity[2] *= 1 - .1 * friction
    spin = [spin[i] + .2 * (i + 1) for i in range(4)]
    case = _u32(ctx, script + 8)
    if case == 11: velocity[2] = -50 if position[2] > 0 else 50
    if case == 14: velocity[1] = .2
    for reg, data in ((5, position), (6, velocity), (7, spin)):
        ctx.write(ctx.r(reg), struct.pack(">4f", *data))
    ctx.write(script + 4, struct.pack(">I", 1))
    ctx.ret()


CALLS = {
    "BallShot_IsLocalPlay": run(),
    "BallShot_RecordNetCrossing": run(),
    "io_Input_poll_9D68": model(poll),
    "BallFlight_Acceleration": model(acceleration, deref={"r5": 16, "r6": 16}),
    "BallFlight_Bounce": model(bounce),
    "bound.vfn_11": model(material, args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    if not getattr(rng, "_simulation_zero_stack", False):
        old = rng.randbytes
        rng.randbytes = lambda n: bytes(n) if n == 0x9000 else old(n)
        rng._simulation_zero_stack = True
    case = t.index % 24
    entry = t.alloc(0x1A0, "shot", floats=[0xBC])
    t.wf32(entry + 0xBC, rng.choice([0, .5, .9, 1]))
    t.w32(entry + 0xCC, rng.choice([3, 8, 9, 10]))
    start = t.alloc(16, "start", floats=[(0, 4)])
    velocity = t.alloc(16, "launch", floats=[(0, 4)])
    spin = t.alloc(16, "spin", floats=[(0, 4)])
    target = t.alloc(16, "target", floats=[(0, 4)])
    result = t.alloc(16, "result", floats=[(0, 4)])
    report = t.alloc(0x30, "contacts", floats=[(0, 10)])
    t.floats(report, 10, -2, 2)
    for off in (0x28, 0x29, 0x2A): t.w8(report + off, rng.choice([0, 1, 2, 0xff]))
    t.floats(spin, 4, -5, 5)
    positions = [(0, 1.4, -.8), (0, .6, -.8), (0, .78, -.2),
        (1.12, .5, -.2), (0, .5, 1.62), (1.12, .5, 1.62), (1.5, .5, -.2),
        (0, .5, -.2), (0, .85, -.02), (0, .85, -0.0), (0, .85, 0.0),
        (0, 1.8, -.02), (0, .9, -.2), (0, 1.4, -.8), (0, 1.4, -.5),
        (0, 1.4, -.5), (0, 1.4, -.5), (0, 1.4, -.5), (1.2, 1.4, -.5),
        (0, 1.4, -.3), (0, 1.4, -.5), (1.5, 1.4, -.5), (0, .4, -.5),
        (0, 1.4, -.5)]
    velocities = [( .3, 1, 4), (0, -1, 0), (0, -1, 0), (-6, .25, .2),
        (0, .25, -6), (-6, .25, -6), (0, 5, .2), (0, 6, .2), (0, 0, 3),
        (0, 0, 3), (0, 0, -3), (0, 0, 3), (0, 1, 0), (0, .1, 0),
        (0, -1, 0), (.2, 0, .3), (.2, 0, .3), (.2, 0, .3), (.2, 0, .3),
        (0, 0, 5), (0, 0, 0), (0, 0, 0), (0, -0.0, 0), (0, 0, 0)]
    for lane, value in enumerate(positions[case]): t.wf32(start + lane * 4, value)
    for lane, value in enumerate(velocities[case]): t.wf32(velocity + lane * 4, value)
    t.wf32(start + 12, rng.choice([0, 1, -1]))
    t.wf32(velocity + 12, rng.uniform(-1, 1))
    for lane, value in enumerate((0, .78, 3 if case in (7, 12) else .5, rng.uniform(-1, 1))):
        t.wf32(target + lane * 4, value)
    first = rng.choice([0, 1, 0x100, 0x101, 0xff])
    if case in (11, 14, 15, 16, 18, 19, 20, 21): first = 1
    if case == 17: first = 0
    stack_flag = rng.choice([1, 0x101, 0x100]) if case in (7, 12) else rng.choice([0, 0x100])
    report_arg = 0 if case == 16 else (report if rng.randrange(5) else 0)
    t.stack_patches[STACK_TOP + 0x54] = struct.pack(">I", report_arg)
    t.stack_patches[STACK_TOP + 8] = struct.pack(">I", report_arg)

    loop = t.alloc(0x210, "loop", floats=[0x208])
    t.wf32(loop + 0x208, 2 if case in (13, 14) else rng.choice([30, 60, 120, 29.49, 29.5, 59.5]))
    t.w32(0x825EAB30, loop)
    poll_script = t.alloc(8, "poll script")
    t.w32(poll_script, rng.choice([0, 1, 0x100, 0x101, 0xffffff00]))
    t.w32(poll_script + 4, rng.choice([0, 1, 0xffffffff]))
    t.w32(0x825EAB28, poll_script)
    t.w32(0x825C9A2C, rng.getrandbits(32))
    t.w8(0x825C5EC8 + 0x30, rng.choice([0, 1, 0xff]))
    t.wf32(0x826064B8, rng.uniform(-.02, .02))
    t.wf32(0x825C8078, rng.choice([.01, .05, -.02]))
    for lane, value in enumerate((0, 1, 0, 0)): t.wf32(0x825CB7A0 + lane * 4, value)
    tables = []
    for n in range(2):
        table = t.alloc(0x20, f"table {n}", floats=[4, (0x10, 3)])
        net = t.alloc(0x90, f"net {n}", floats=[(0x80, 2)])
        t.w32(table, net)
        t.wf32(table + 4, rng.uniform(.1, 2))
        t.wf32(table + 0x10, 2 if n == 0 else rng.uniform(1, 3))
        t.wf32(table + 0x14, .76 if n == 0 else rng.uniform(.5, 1))
        t.wf32(table + 0x18, 3 if n == 0 else rng.uniform(2, 4))
        t.wf32(net + 0x80, .15)
        t.wf32(net + 0x84, .75)
        tables.append(table)
    t.w32(0x8271A304, tables[0])
    material_ptr = t.alloc(16, "material", floats=[12])
    t.wf32(material_ptr + 12, rng.uniform(.1, 1.5))
    bound = t.alloc(16, "bound", floats=[8])
    t.w32(bound, t.vtable("bound", 12))
    t.wf32(bound + 8, .02)
    arch = t.alloc(0x10, "archetype")
    t.w32(arch, t.vtable("arch", 13))
    t.w32(arch + 12, bound)
    inst = t.alloc(8, "ball")
    t.w32(inst + 4, arch)
    slot = t.alloc(4, "ball slot")
    t.w32(slot, inst)
    t.w32(0x8271A2F4, slot)
    script = t.alloc(64, "simulation script", fill="zero", floats=[(16, 5), 48])
    SCRIPT[0] = script
    t.w32(script + 8, case)
    t.w32(script + 12, int(case == 15 or rng.randrange(3) == 0))
    for lane, value in enumerate((rng.choice([0, .2, 1e-40]), 0 if case == 13 else -9.8,
                                  rng.choice([0, -.1, -1e-40]), rng.choice([0, 1e-40]))):
        t.wf32(script + 16 + lane * 4, value)
    t.wf32(script + 32, rng.choice([0, .02]))
    for off, value in ((36, tables[1]), (40, material_ptr), (44, entry)): t.w32(script + off, value)
    t.wf32(script + 48, rng.choice([.3, .7, 1]))
    t.args(r3=entry, r4=start, r5=velocity, r6=spin, r7=target,
           r8=first, r9=result, r10=stack_flag)
