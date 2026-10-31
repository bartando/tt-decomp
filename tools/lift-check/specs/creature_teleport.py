"""0x820C7A28: teleport flags, worker pose snapshots and cache invalidation.

All flag combinations, absent/shared workers, both copy/reset phases, zero/many
cache entries and optional secondary cache. Callbacks change workers, skeleton,
player index, table, frame buffer and frame cursor to verify snapshot/reload
ordering. Every output byte, guard, pointee and callback argument is compared.
"""
import struct
from liftcheck.spec import *

FUNCTION = "pongCreature_Teleport"
ADDRESS = 0x820C7A28
SOURCE = "src/game/creature/pong_creature.cpp"
TRIALS = 800
EXTERNS = {"g_plrPlayerMgr_state": 0x82606430, "g_large_buffer_ptr": 0x8260637C,
           "g_phFrameIndex": 0x826065DC}


def u(ctx, address):
    return int.from_bytes(ctx.read(address, 4), 'big')


def wu(ctx, address, value):
    ctx.write(address, struct.pack('>I', value))


def update(ctx):
    creature = ctx.r(3)
    character = u(ctx, creature + 0xA0)
    data = u(ctx, character + 0x14)
    ctx.write(data + 0xD8, bytes(8))


def move(ctx):
    inst = ctx.r(3)
    creature = u(ctx, inst + 0xD0)
    skeleton, table, buffer, frame, player = struct.unpack('>5I', ctx.read(creature + 0x170, 20))
    wu(ctx, creature + 0xAC, skeleton)
    wu(ctx, creature + 0xCC, player)
    wu(ctx, 0x82606430, table)
    wu(ctx, 0x8260637C, buffer)
    wu(ctx, 0x826065DC, frame)


def reset(ctx):
    worker = ctx.r(3)
    creature = u(ctx, worker + 0x80)
    # Next worker must get the latest skeleton.
    wu(ctx, creature + 0xAC, u(ctx, creature + 0x188))
    other_pose = u(ctx, worker + 0x84)
    if other_pose:
        # Both pose copies must already have completed before this callback.
        ctx.write(other_pose + 0xB0, b'\x5A' * 80)


CALLS = {
    0x8240E6D0: stub(ret="void", args=("r4", "f1", "f2", "f3"),
                     deref={"r3": len('pongCreature::Teleport() - teleporting player[%d] to [%f,%f,%f]') + 1}),
    0x820C69A0: model(update, args=("r3",)),
    0x820C8FA8: model(move, args=("r3", "r4"), deref={"r4": 64}),
    0x820FAB78: model(reset, args=("r3", "r4")),
}


def inputs(t):
    rng = t.rng
    creature = t.alloc(0x1A0, 'creature and callback script')
    character = t.alloc(0x20, 'character')
    data = t.alloc(0xE0, 'character data')
    inst = t.alloc(0xE0, 'instance')
    skeletons = [t.alloc(0x20, f'skeleton {i}') for i in range(3)]
    t.w32(creature + 0xA0, character)
    t.w32(character + 0x14, data)
    t.w32(creature + 0xA4, inst)
    t.w32(inst + 0xD0, creature)
    t.w32(creature + 0xAC, skeletons[0])
    t.w32(creature + 0x170, skeletons[1])
    t.w32(creature + 0x188, skeletons[2])
    workers, poses = [], []
    for i in range(2):
        worker = t.alloc(0xA0, f'worker {i}')
        pose = t.alloc(0x110, f'pose {i}')
        root = t.alloc(0x60, f'root {i}')
        t.floats(root + 0x10, 16, -10, 10)
        t.w32(worker + 0x24, pose)
        t.w32(worker + 0x80, creature)
        t.w32(pose, root)
        workers.append(worker)
        poses.append(pose)
    t.w32(workers[0] + 0x84, poses[1])
    t.w32(workers[1] + 0x84, 0)
    kind = (t.index // 8) % 5
    chosen = ((0, 0), (workers[0], 0), (0, workers[1]), tuple(workers), (workers[0], workers[0]))[kind]
    t.w32(data + 0xD8, chosen[0])
    t.w32(data + 0xDC, chosen[1])
    tables = [t.alloc(256 * 4, f'player table {i}') for i in range(2)]
    for table in tables:
        for player in (0, 1, 7):
            index = 70 + player * 3
            t.w32(table + (player + 33) * 4, index)
            signals = t.alloc(0x1830, 'cache signals')
            entries = t.alloc(32, 'cache entries')
            count = rng.randrange(9)
            for i in range(8):
                target = t.alloc(0x50, f'cache entry {i}')
                t.w32(entries + 4 * i, target)
            t.w32(signals + 0x1814, entries)
            t.w16(signals + 0x1818, count)
            secondary = t.alloc(0xB0, 'secondary cache') if rng.randrange(2) else 0
            t.w32(signals + 0x181C, secondary)
            t.w32(table + (index + 29) * 4, signals)
    buffers = [t.alloc(0x100, f'frame buffer {i}') for i in range(2)]
    t.w32(0x82606430, tables[0])
    t.w32(0x8260637C, buffers[0])
    t.w32(0x826065DC, rng.choice((0, 16, 64)))
    t.w32(creature + 0x174, tables[1])
    t.w32(creature + 0x178, buffers[1])
    t.w32(creature + 0x17C, rng.choice((0, 16, 64)))
    t.w32(creature + 0x180, rng.choice((0, 1, 7)))
    t.w32(creature + 0xCC, rng.choice((0, 1, 7)))
    matrix = creature + 0x110 if t.index % 2 else t.alloc(64, 'matrix')
    t.floats(matrix, 16, -20, 20)
    t.args(r3=creature, r4=matrix, r5=t.index & 1, r6=(t.index >> 1) & 1,
           r7=(t.index >> 2) & 1)
