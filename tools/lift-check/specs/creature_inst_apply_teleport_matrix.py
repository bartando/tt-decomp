"""0x820C8FA8: sequential matrix rows, live owner and physics location updates.

Callbacks replace the owner, instance vtable and level index/global. Compare all
calls and memory, including partially overlapping matrix/instance storage.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongCreatureInst_ApplyTeleportMatrix"
ADDRESS = 0x820C8FA8
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 600
EXTERNS = {"g_pPhysicsLevel": 0x826065E4}


def set_last(ctx):
    inst = ctx.r(3)
    owner, vtable, level, index = struct.unpack('>4I', ctx.read(inst + 0x130, 16))
    ctx.write(inst + 0xD0, struct.pack('>I', owner))
    ctx.write(inst, struct.pack('>I', vtable))
    ctx.write(inst + 8, struct.pack('>H', index))
    ctx.write(0x826065E4, struct.pack('>I', level))


CALLS = {
    0x8214C8F8: stub(ret="void", args=("r3",)),
    "initial.vfn_3": model(set_last, args=("r3", "r4"), deref={"r4": 64}),
    0x820C6B68: stub(ret="void", args=("r3",)),
    "changed.vfn_47": stub(ret="void", args=("r3",)),
    "level.vfn_11": stub(ret="void", args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    inst = t.alloc(0x160, "instance with script")
    t.w32(inst, t.vtable('initial', 48))
    owners = [t.alloc(0x170, f'owner {i}') for i in range(2)]
    for owner in owners:
        t.w32(owner + 0xAC, t.alloc(0x20, 'skeleton'))
    t.w32(inst + 0xD0, owners[0])
    t.w16(inst + 8, rng.choice((0xFFFF, 0, 123)))
    level = t.alloc(0x30, 'level')
    t.w32(level, t.vtable('level', 12))
    t.w32(t.sym('g_pPhysicsLevel'), level)
    t.w32(inst + 0x130, owners[1])
    t.w32(inst + 0x134, t.vtable('changed', 48))
    t.w32(inst + 0x138, level)
    t.w32(inst + 0x13C, rng.choice((0, 123, 0xFFFF)))
    storage = t.alloc(96, 'matrix with guards')
    matrix = inst + rng.choice((0x10, 0x20, 0x30)) if t.index % 4 else storage + 16
    t.floats(matrix, 16, -10, 10)
    t.args(r3=inst, r4=matrix)
