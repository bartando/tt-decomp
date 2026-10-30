"""0x82339240: inferred clothCollideMesh, formerly pongCreatureInst_9240_2hr.

Execute the original response callee using the existing VMX bridge, comparing
all scalar/vector call arguments, call order and external writes. No ignored
memory or patched instructions. Cover face-cache writes, sentinels, all three
edge choices, strict/tied boundaries, the eight-hop budget, the asymmetric
backtracking guard, the first-face distance used for neighbour contacts,
-0.05 cutoff, empty/pinned/negative-start ranges, mode-1 response, misaligned
vector loads, nonuniform lanes, nonfinite/subnormal values and live input aliasing.

Limits: lift-check's VMX/dot model and exact estimate instructions stand in for
Xenon hardware. FTOL allows rounding differences in the running response; NaN
payloads/signs are not compared. The portable C++ response requires a VMX ABI
bridge in a running recompilation; this spec supplies that bridge only here.
"""
from liftcheck.spec import *
from specs.cloth_collide_capsule import VmxCall, vector, f32

FUNCTION = "clothCollideMesh"
ADDRESS = 0x82339240
SOURCE = "src/game/match/lvl_table.cpp"
FP_CONTRACT = "off"
FTOL = 1e-6
TRIALS = 1200
CALLS = {
    "lvlTable_7008_2h": VmxCall(("r3", "r4", "r5"), ((1, 6), (2, 7), (3, 8))),
}


def inputs(t):
    rng = t.rng
    case = rng.randrange(40)
    count = rng.choice((0, 1, 2, 4, 9, 16)) if case == 0 else rng.randrange(1, 10)
    first = rng.randrange(count + 3) if case == 0 else rng.randrange(count)
    if case == 30:
        first = -1
    self = t.alloc(0x170, "cloth", ctype="ClothMeshCollisionView")
    bound = t.alloc(0x90, "mesh", ctype="ClothMeshBoundView")
    faces = t.alloc(12 * 32, "faces")
    vertices = t.alloc(36 * 16, "vertices")
    positions = t.alloc((count + 1) * 16, "positions") + 16
    previous = t.alloc((count + 1) * 16, "previousPositions") + 16
    caches = t.alloc(8, "cachePointers")
    cache = t.alloc(max(16, (count + 1) * 2), "cachedFaces") + 2
    reduction = t.alloc(16, "reduction")
    expansion = t.alloc(16, "expansion")
    t.w32(bound + 0x74, vertices + rng.randrange(16))
    t.w32(bound + 0x7C, faces)
    t.w32(self + 8, first)
    t.w16(self + 0x20, count)
    t.w32(self + 0x2C, caches)
    t.w32(caches, cache)
    t.w32(caches + 4, 0)  # later cache entries must never be used

    padding = [0.5] * 4
    shrink = [0.1] * 4
    mode = rng.choice((0, 1, 2, 0xFFFF, 0xABCD0001, 0x10000))
    for face in range(12):
        # Distinct planes let the spec distinguish first vs neighbour distance.
        z = 0.0 if face == 0 else rng.choice((-0.4, 0.0, 0.25, 0.75))
        offset = 0.0
        offset_y = 0.0
        if face == 1 and case in (5, 8, 11):
            offset_y = -1.0
            z = 0.75 if case == 5 else -0.4
        elif face == 1 and case in (6, 9, 12):
            offset = -1.0
            z = 0.75 if case == 6 else 0.0
        normal = [0.0, 0.0, 1.0, rng.choice((0.0, -1.0, 2.0))]
        if case >= 32:
            offset = rng.uniform(-2, 2)
            normal = [rng.uniform(-1, 1) for _ in range(4)]
        elif case == 25:
            normal = [0.0, 0.0, f32(1), 1.0]  # VMX flushes denormal inputs
        elif case == 26:
            normal[2] = float("nan")
        elif case == 27:
            normal[3] = float("nan")  # dot3 ignores w, response preserves it
        elif case == 28:
            normal[2] = float("inf")
        vector(t, faces + face * 32, normal)
        points = ([offset, offset_y, z, 0.0], [offset + 1.0, offset_y, z, 1.0],
                  [offset, offset_y + 1.0, z, -1.0])
        if case == 31:  # degenerate face and tied edge scores
            points = ([0.0, 0.0, 0.0, 0.0],) * 3
        for k, point in enumerate(points):
            vector(t, vertices + (face * 3 + k) * 16, point)
            t.w16(faces + face * 32 + 0x10 + k * 2, face * 3 + k)
            neighbour = rng.choice((0xFFFF, *range(12)))
            if case < 24:
                neighbour = (face + 1) % 12
            if case in (1, 2, 3):
                neighbour = 0xFFFF
            if case in (20, 21):
                neighbour = face if k == 2 else (face + 1) % 12
            if case == 21:
                neighbour = (face + k + 1) % 12
            t.w16(faces + face * 32 + 0x18 + k * 2, neighbour)

    for particle in range(-1, count):
        x, y = rng.choice(((0.2, 0.2), (-0.5, 0.2), (0.2, -0.5), (1.0, 1.0),
                           (0.0, 0.0), (0.5, 0.5), (-1.0, -1.0), (2.0, -1.0)))
        z = rng.choice((-0.2, -0.05, 0.0, 0.25, 0.5, 0.75))
        if case in (1, 4, 7, 10):
            x, y = 0.2, 0.2
        if case in (2, 5, 8, 11):
            x, y = 0.2, -0.5
        if case in (3, 6, 9, 12):
            x, y = -0.5, 0.2
        if case in (4, 5, 6):
            z = 0.75
        if case in (7, 8, 9):
            z = -0.2
        if case == 8:
            z = -0.025
        if case == 9:
            z = -0.05
        if case == 21:
            x, y, z = 3.0, -1.0, 0.25
        if case == 13:
            z = f32(0xBD4CCCCD)  # exactly the loaded -0.05f cutoff
        if case == 14:
            z = f32(0xBD4CCCCE)
        if case == 15:
            z = f32(0xBD4CCCCC)
        if case == 16:
            z = 0.5
        if case == 17:
            z = f32(0x3F000001)
        if case == 18:
            z = f32(1)
        if case == 19:
            x, y, z = 0.0, 0.0, -0.0
        if case == 22:
            padding = [-0.5] * 4
        if case == 23:
            padding = [0.1, 0.8, -0.1, 12.0]
            shrink = [-0.2, 0.3, 0.7, -0.4]
        if case == 24:
            x = float("nan")
        if case == 29:
            z = float("inf")
        if case >= 32:
            x, y, z = [rng.uniform(-2, 2) for _ in range(3)]
            padding = [rng.uniform(-0.5, 1) for _ in range(4)]
            shrink = [rng.uniform(-0.5, 1) for _ in range(4)]
        vector(t, positions + particle * 16, [x, y, z, rng.choice((0.0, 1.0, -2.0))])
        vector(t, previous + particle * 16, [rng.uniform(-2, 2) for _ in range(4)])
        t.w16(cache + particle * 2, rng.choice((0xFFFF, *range(12))) if case >= 30 else 0)
    vector(t, reduction, shrink)
    vector(t, expansion, padding)
    # Supply the complete live state consumed by mode-1 particle response.
    t.floats(self + 0x50, 8, -1, 1)
    t.floats(self + 0x70, 4, 0, 3)
    t.floats(self + 0x160, 4, -1, 1)
    transforms = t.alloc(64, "transform")
    transform_indices = t.alloc(4, "transformIndices")
    t.w32(transform_indices, 0)
    t.w32(self + 0x140, transforms)
    t.w32(self + 0x148, transform_indices)
    t.w32(self + 0x150, 0)
    for row in range(4):
        vector(t, transforms + row * 16, [float(row == col) for col in range(4)])
    if case == 36:
        reduction = positions + first * 16
    elif case == 37:
        expansion = positions + first * 16
    elif case == 38:
        previous = positions
    t.w32(self + 0x1C, positions + rng.randrange(16))
    t.w32(self + 0x24, previous + rng.randrange(16))
    t.args(r3=self, r4=bound, r5=reduction + rng.randrange(16),
           r6=expansion + rng.randrange(16), r7=mode)
