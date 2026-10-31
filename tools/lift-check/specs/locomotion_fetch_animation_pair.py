"""0x8224C358: ID-zero channel pair, aligned translation and scalar quaternion.

Real lookup covers hits/misses, high type bits and identical channels. Getter14
replaces getter15's vtable and empties the lookup list: both lookups must precede
it, but the second dispatch must be live. Inputs cover output/source aliasing,
misaligned vector pointers and overlapping scalar quaternion stores.
"""
import struct
from liftcheck.spec import *

FUNCTION = 'LocomotionStateAnim_C358_g'
ADDRESS = 0x8224C358
SOURCE = 'src/game/creature/pong_creature.cpp'
TRIALS = 400


def u(c, a): return int.from_bytes(c.read(a, 4), 'big')


def translation(c):
    entry = c.r(3)
    second, changed, frame = struct.unpack('>3I', c.read(entry + 0x30, 12))
    c.write(second, struct.pack('>I', changed))
    c.write(frame + 0x0C, b'\x00\x00')
    c.ret(r3=u(c, entry + 0x20))


def quaternion(c): c.ret(r3=u(c, c.r(3) + 0x24))


CALLS = {
    'LocomotionStateAnim::FindAnimationByID': run(),
    'initial.vfn_14': model(translation, args=('r3',)),
    'changed.vfn_15': model(quaternion, args=('r3',)),
    'initial.vfn_15': model(quaternion, args=('r3',)),
    'changed.vfn_14': model(lambda c: c.ret(r3=u(c,c.r(3)+0x20)), args=('r3',)),
}


def inputs(t):
    rng = t.rng
    mode = t.index % 8
    first_type = rng.randrange(256)
    second_type = first_type if mode in (4, 5) else first_type ^ 1
    keys = {(rng.randrange(256), rng.randrange(1, 65536)) for _ in range(rng.randrange(6))}
    if mode not in (1, 3, 5): keys.add((first_type, 0))
    if mode not in (2, 3, 5): keys.add((second_type, 0))
    frame = t.alloc(0x30, 'lookup frame')
    table = t.alloc(max(4, len(keys)*4), 'sorted channels')
    initial, changed = t.vtable('initial', 19), t.vtable('changed', 19)
    entries = {}
    for i, key in enumerate(sorted(keys)):
        entry = t.alloc(0x50, 'channel')
        t.w32(table + i*4, entry)
        t.w32(entry, initial)
        t.w8(entry + 5, key[0])
        t.w16(entry + 6, key[1])
        entries[key] = entry
    t.w32(frame + 8, table if keys else 0)
    t.w16(frame + 12, len(keys))
    vector = t.alloc(64, 'translation and guards') + 16
    q = t.alloc(64, 'quaternion and guards') + 16
    out = t.alloc(96, 'output and guards') + 16 + rng.randrange(4)*4
    t.floats(vector, 8, -50, 50)
    t.floats(q, 8, -3, 3)
    for entry in entries.values():
        t.w32(entry + 0x20, vector)
        t.w32(entry + 0x24, q)
    if mode == 6: out = q + 4
    if mode == 7: out = vector
    if (first_type, 0) in entries and (second_type, 0) in entries:
        first, second = entries[first_type, 0], entries[second_type, 0]
        t.w32(first + 0x20, vector + rng.randrange(16))
        t.w32(second + 0x24, q)
        t.w32(first + 0x30, second)
        t.w32(first + 0x34, changed)
        t.w32(first + 0x38, frame)
    else:
        out = 0 if mode in (1, 2, 3) else out
    t.args(r3=frame, r4=first_type | rng.getrandbits(24) << 8,
           r5=second_type | rng.getrandbits(24) << 8,
           r6=rng.getrandbits(32), r7=out)
