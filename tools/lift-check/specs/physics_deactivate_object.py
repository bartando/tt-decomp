"""0x822C4B60: pooled collider reclamation, level removal, cached body dispatch."""
import struct
from liftcheck.spec import *

FUNCTION = "game_4B60"
ADDRESS = 0x822C4B60
SOURCE = "src/physics/ph_update_object.cpp"
TRIALS = 1000


def u32(ctx, addr):
    return struct.unpack(">I", ctx.read(addr, 4))[0]


def collider(ctx):
    level = ctx.r(3)
    scene = u32(ctx, level + 8)
    ctx.write(scene + 4, struct.pack(">I", u32(ctx, level + 12)))
    ctx.ret(r3=u32(ctx, level + 4))


def remove(ctx):
    level = ctx.r(3)
    # The final call must retain the body read before level removal.
    ctx.write(u32(ctx, level + 4) + 0x10,
              struct.pack(">I", u32(ctx, level + 16)))


CALLS = {
    "level.vfn_4": model(collider, args=("r3", "r4")),
    "level.vfn_20": model(remove, args=("r3", "r4")),
    "body.vfn_18": stub(ret="void", args=("r3",)),
}


def inputs(t):
    rng = t.rng
    scene = t.alloc(0x30, "simulator")
    pool_storage = t.alloc(0x1D0 * 20, "collider pool")
    pool = pool_storage + 0x1D0 * 5
    capacity = rng.choice([0, 1, 2, 5, 8])
    # Signed division rounds negative partial strides to zero. Include exact
    # capacity boundaries, outside-pool colliders, and unaligned positive slots.
    offset = rng.choice([-0x1D0 * 3, -0x1D0, -0x1CC, -4, 0, 4, 0x1CC,
                         0x1D0, 0x1D0 + 4, 0x1D0 * capacity,
                         0x1D0 * (capacity + 1), 0x1D0 * 3])
    active = pool + offset
    bodies = [t.alloc(4, "body"), t.alloc(4, "replacement body")]
    for body in bodies:
        t.w32(body, t.vtable("body", 20))
    t.w32(active + 0x10, bodies[0])
    levels = [t.alloc(32, "initial level"), t.alloc(32, "replacement level")]
    next_level = rng.choice(levels)
    for level in levels:
        t.w32(level, t.vtable("level", 24))
        t.w32(level + 4, active)
        t.w32(level + 8, scene)
        t.w32(level + 12, next_level)
        t.w32(level + 16, bodies[1])
    free_indices = t.alloc(32, "free collider indices")
    t.w32(scene + 4, levels[0])
    t.w32(scene + 0x10, capacity)
    t.w32(scene + 0x14, rng.randrange(1, 16))
    t.w32(scene + 0x18, pool)
    t.w32(scene + 0x24, free_indices)
    t.args(r3=scene, r4=rng.choice([0, 1, 255, 32768, 65535, rng.randrange(65536)]))
