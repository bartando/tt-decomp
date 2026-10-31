"""0x820FAB78: pose selection, skinning, CPU position copies and bound resets.

Snapshot/inverse/composition/skinning/map/unmap are modeled at their boundaries;
the skin model asserts the complete pose against those scripted operations.
Callbacks replace geometry, buffer mapping/stride/count, worker part and child
bound tables. Check every call and memory byte except destination w: PPC never
writes its scratch w. A missing first CPU position is itself undefined; test
CPU-unavailable carry only after a successful first fetch. Zero/many bones and
vertices, ring selection, duplicate/wrapping output indices and bound gates.
"""
import struct
from liftcheck.spec import *

FUNCTION = 'pongCreatureWorker_Reset'
ADDRESS = 0x820FAB78
SOURCE = 'src/game/creature/creature_pose.cpp'
TRIALS = 480
EXTERNS = {'g_creatureWorkerRelativePose': 0x825C9F54,
           'g_renderClearRingIdx': 0x82606348}


def u(c, a): return int.from_bytes(c.read(a, 4), 'big')
def wu(c, a, v): c.write(a, struct.pack('>I', v))
def fs(c, a, n): return struct.unpack('>' + 'f'*n, c.read(a, n*4))
def packed(values): return struct.pack('>' + 'f'*len(values), *values)
def f32(v): return struct.unpack('>f', struct.pack('>f', v))[0]


def snapshot(c):
    script = u(c, c.r(3) + 0x30)
    count, template, relative, root, geometry, worker = struct.unpack('>6I', c.read(script, 24))
    c.write(c.r(4), c.read(template, count * 64))
    wu(c, 0x825C9F54, relative)
    wu(c, worker + 0x3C, geometry)


def inverse(c):
    c.write(c.r(3), packed([f32(v + 10.) for v in fs(c, c.r(3), 16)]))


def compose(c):
    a, b = fs(c, c.r(3), 16), fs(c, c.r(4), 16)
    c.write(c.r(3), packed([f32(x + y) for x, y in zip(a, b)]))


def skin(c):
    script = u(c, c.r(3) + 0xE0)
    count, template, relative, root, geometry, worker, skinmap, source = struct.unpack('>8I', c.read(script, 32))
    expected = list(fs(c, template, count * 16))
    if relative:
        root_matrix = [f32(v + 10.) for v in expected[root*16:root*16+16]]
        expected = [f32(v + root_matrix[i % 16]) for i, v in enumerate(expected)]
    assert c.r(5) == count, 'wrong saved bone count'
    assert c.r(6) == skinmap and c.r(7) == 0 and c.r(9) == source, 'wrong skinning arguments'
    assert c.read(c.r(4), count * 64) == packed(expected), 'wrong complete skinning pose'
    wu(c, source, u(c, script + 32))
    c.write(source + 0xDB, bytes([u(c, script + 36)]))
    c.write(source + 0x3E, b'\x01')
    wu(c, worker + 0x24, u(c, script + 60))


def map_buffer(c):
    buffer = c.r(3)
    script = u(c, buffer + 0xE0)
    wu(c, buffer, u(c, script + 40))
    wu(c, buffer + 0x1C, u(c, script + 44))
    wu(c, buffer + 0xD4, u(c, script + 48))
    c.write(buffer + 0x3E, bytes([u(c, script + 52)]))
    c.write(buffer + 0xDB, b'\x01')
    wu(c, u(c, script + 20) + 0x24, u(c, script + 56))
    c.ret(r3=1)


def unmap_buffer(c):
    script = u(c, c.r(3) + 0xE0)
    wu(c, u(c, script + 20) + 0x24, u(c, script + 64))
    c.ret(r3=1)


def parent_bound(c):
    bound = c.r(3)
    part, indices, children, count = struct.unpack('>4I', c.read(bound + 0x80, 16))
    wu(c, part + 0x100, indices)
    c.write(part + 0x104, struct.pack('>H', count))
    wu(c, bound + 0x70, children)
    c.write(bound + 5, bytes([c.r(4)]))


CALLS = {
    0x82569394: run(transparent=True, args=()),
    0x8214CD70: model(snapshot, args=('r3', 'r4')),
    0x820D5040: model(inverse, args=('r3',), deref={'r3': 64}),
    0x820C3AD8: model(compose, args=('r3', 'r4'), deref={'r3': 64, 'r4': 64}),
    0x82155510: model(skin, args=('r3', 'r4', 'r5', 'r6', 'r7', 'r8', 'r9')),
    0x82157578: model(map_buffer, args=('r3',)),
    0x82157628: model(unmap_buffer, args=('r3',)),
    'parent.vfn_1': model(parent_bound, args=('r3', 'r4')),
    'child.vfn_1': model(lambda c: c.write(c.r(3) + 5, bytes([c.r(4)])), args=('r3', 'r4')),
}


def inputs(t):
    rng = t.rng
    worker = t.alloc(0x90, 'worker')
    skeleton = t.alloc(0x40, 'input skeleton')
    script = t.alloc(0x60, 'callback script')
    count = (0, 1, 2, 4, 7)[t.index % 5]
    template = t.alloc(max(64, count * 64), 'pose template')
    t.floats(template, max(16, count * 16), -5, 5)
    t.w32(skeleton + 0x30, script)
    relative = rng.choice((0, 1, 255)) if count else 0
    root = rng.randrange(count) if count else 0
    t.w32(script, count)
    t.w32(script + 4, template)
    t.w32(script + 8, relative)
    t.w32(script + 12, root)
    t.w32(script + 20, worker)
    t.w32(0x825C9F54, 0 if relative else 1) # snapshot changes it
    ring = rng.randrange(2)
    t.w32(0x82606348, ring)
    mesh_slot, mesh_index, batch_index = (rng.randrange(3) for _ in range(3))
    t.w32(worker + 0x40, mesh_slot)
    t.w32(worker + 0x44, mesh_index)
    t.w32(worker + 0x48, batch_index)
    geometries, chosen = [], []
    for version in range(2):
        geometry = t.alloc(0x60, f'geometry {version}')
        data = t.alloc(0x20, f'skeleton metadata {version}')
        t.w32(geometry + 8, data)
        t.w16(data + 12, count)
        geometries.append(geometry)
        for slot in range(3):
            table = t.alloc(16, 'mesh table')
            meshes = t.alloc(16, 'mesh pointers')
            t.w32(geometry + 0x40 + slot * 4, table)
            t.w32(table, meshes)
            for index in range(3):
                mesh = t.alloc(0x20, 'mesh')
                batches = t.alloc(120, 'batches')
                t.w32(meshes + index * 4, mesh)
                t.w32(mesh + 4, batches)
                t.w8(mesh + 0x13, root if slot == mesh_slot and index == mesh_index else 0)
                for batch in range(3):
                    buffers = t.alloc(0x40, 'buffer set')
                    skinmap = t.alloc(16, 'skin map')
                    t.w32(batches + batch * 40, buffers)
                    ringed = rng.choice((0, 1, 255))
                    t.w8(batches + batch * 40 + 0x25, ringed)
                    t.w32(buffers + 0x38, skinmap)
                    for bank in range(2):
                        buffer = t.alloc(0x100, 'source buffer')
                        positions = t.alloc(8*32, 'initial vertices')
                        t.floats(positions, 64, -20, 20)
                        t.w32(buffer, rng.randrange(7))
                        t.w32(buffer + 0x1C, positions)
                        t.w32(buffer + 0xD4, 32)
                        t.w32(buffer + 0xE0, script)
                        t.w32(buffers + bank * 4, buffer)
                        if (slot, index, batch, bank) == (mesh_slot, mesh_index, batch_index, ring if ringed else 0):
                            chosen.append((version, buffer, skinmap))
    t.w32(worker + 0x3C, geometries[0])
    t.w32(script + 16, geometries[1])
    _, selected, skinmap = next(v for v in chosen if v[0] == 1)
    t.w32(script + 24, skinmap)
    t.w32(script + 28, selected)
    destination = t.alloc(0x100, 'destination buffer')
    t.w32(destination + 0xE0, script)
    t.w32(worker + 0x6C, destination)
    after_skin = rng.randrange(7)
    mapped = rng.choice((0, 1, 255))
    after_map = rng.randrange(7)
    new_vertices = t.alloc(8*32, 'mapped vertices')
    t.floats(new_vertices, 64, -50, 50)
    stride = rng.choice((16, 32))
    t.w32(script + 32, after_skin)
    t.w32(script + 36, mapped)
    t.w32(script + 40, after_map)
    t.w32(script + 44, new_vertices)
    t.w32(script + 48, stride)
    t.w32(script + 52, rng.choice((0, 1, 255)))
    mapping = t.alloc(32, 'worker vertex mapping')
    indices = [rng.randrange(8) | rng.choice((0, 0x10000000, 0xF0000000)) for _ in range(8)]
    for i, value in enumerate(indices): t.w32(mapping + i*4, value)
    t.w32(worker + 0x28, mapping)
    parts, arrays = [], []
    for i in range(3):
        part = t.alloc(0x120, f'part {i}')
        a, b = [t.alloc(160, f'part {i} positions {j}') + 16 for j in range(2)]
        t.w32(part + 0x1C, a)
        t.w32(part + 0x24, b)
        parts.append(part)
        arrays.append((a, b))
    t.w32(worker + 0x24, parts[0])
    t.w32(script + 56, parts[0])
    t.w32(script + 60, parts[1])
    t.w32(script + 64, parts[2])
    iterations = after_skin if mapped or not after_skin else max(1, after_map)
    active = 1 if mapped else 0
    for i in range(iterations):
        for array in arrays[active]:
            # Only w is unwritten scratch data in the original.
            t.ignore(array + (indices[i] & 0x0FFFFFFF) * 16 + 12, 4)
    root_obj = t.alloc(16, 'bound root')
    archetype = t.alloc(16, 'archetype')
    bound = t.alloc(0xA0, 'parent bound')
    gate = (t.index // 5) % 5
    t.w32(parts[2], 0 if gate == 0 else root_obj)
    t.w32(root_obj + 4, 0 if gate == 1 else archetype)
    t.w32(archetype + 12, 0 if gate == 2 else bound)
    t.w32(bound, t.vtable('parent', 2))
    t.w8(bound + 4, 8 if gate == 3 else 9)
    children = t.alloc(16, 'child bound table')
    child_indices = t.alloc(16, 'child indices')
    for i in range(4):
        child = t.alloc(16, f'child bound {i}')
        t.w32(child, t.vtable('child', 2))
        t.w32(children + i*4, child)
        t.w32(child_indices + i*4, rng.randrange(4))
    t.w32(bound + 0x70, t.alloc(16, 'stale child table'))
    t.w32(parts[2] + 0x100, t.alloc(16, 'stale child indices'))
    t.w16(parts[2] + 0x104, 0)
    for offset, value in ((0x80, parts[2]), (0x84, child_indices), (0x88, children), (0x8C, rng.randrange(5))):
        t.w32(bound + offset, value)
    t.args(r3=worker, r4=skeleton)
