"""0x8224F040: correct limit/damping/timestep ABI and per-stage pointer reloads.

Callees are modeled, allowing them to change the collider's joint-data pointer.
Each stage checks receiver, float arguments, and order. No float tolerance.
"""
from liftcheck.spec import *

FUNCTION = "rage::phArticulatedCollider::SetTimestep"
ADDRESS = 0x8224F040
SOURCE = "src/physics/ph_physics.cpp"
TRIALS = 400
FTOL = 1e-99


def stage(ctx):
    import struct
    data = ctx.r(3)
    owner, replacement = struct.unpack('>II', ctx.read(data + 0x200, 8))
    ctx.write(owner + 0x1D0, struct.pack('>I', replacement))
    ctx.ret()


CALLS = {
    "phArticulatedCollider_5FE0": model(stage),
    "phArticulatedCollider_60F8": model(stage),
    "ph_IntegrateJointPositions": model(stage),
    "phArticulatedCollider_RestoreVelocities": model(stage),
    "phArticulatedCollider_8450": model(stage),
    "phArticulatedCollider_F0E0": stub(ret="void"),
    "phArticulatedCollider_5D58": stub(ret="void"),
}


def inputs(t):
    collider = t.alloc(0x250, "colliderAndGuards")
    array = [t.alloc(0x220, f"jointData{i}") for i in range(5)]
    for i, data in enumerate(array):
        t.w32(data + 0x200, collider)
        t.w32(data + 0x204, array[(i + 1) % len(array)])
    t.w32(collider + 0x1D0, array[0])
    timestep = t.rng.choice((0., 1/60, 1/30, 1., -1., 0.001, t.rng.uniform(-1, 2)))
    t.args(r3=collider, f1=timestep)
