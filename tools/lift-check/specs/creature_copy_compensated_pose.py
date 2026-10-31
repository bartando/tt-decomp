"""0x8214CD70: reverse bone snapshots with default/override rest positions.

Exercise bank-pair stride, zero/one/many bones, all four lanes and overlapping
output/source in both directions. Compare all memory exactly, with subnormal
VMX operands/results and arbitrary padding. Finite bounded inputs; default FP
rounding. The reverse walk and row copy/reload order are observable on overlaps.
"""
from liftcheck.spec import *

FUNCTION = "LocomotionState_CD70_g"
ADDRESS = 0x8214CD70
SOURCE = "src/game/creature/creature_pose.cpp"
TRIALS = 1200
FP_CONTRACT = "off"


def inputs(t):
    rng = t.rng
    count = (0, 1, 2, 3, 7, 16)[t.index % 6]
    skeleton = t.alloc(0x40, 'skeleton')
    data = t.alloc(0x20, 'skeleton data')
    bindings = t.alloc(max(16, count * 0xC0), 'bind data')
    banks = t.alloc(64, 'matrix bank pairs')
    bank = rng.randrange(4)
    storage = t.alloc((count + 4) * 64, 'pose matrices and guards')
    source = storage + 128
    t.floats(source, count * 16, -10, 10)
    t.w32(skeleton + 4, data)
    t.w32(data, bindings)
    t.w16(data + 0x0C, count)
    t.w32(skeleton + 0x18, banks)
    t.w16(skeleton + 0x22, bank)
    for slot in range(8):
        other = t.alloc(max(64, count * 64), f'alternate bank slot {slot}')
        t.floats(other, max(16, count * 16), -20, 20)
        t.w32(banks + slot * 4, other)
    t.w32(banks + bank * 8, source)
    override = t.alloc(0x10, 'override') if (t.index // 36) % 2 else 0
    rests = t.alloc(max(16, count * 16), 'rest position overrides')
    t.w32(skeleton + 0x24, override)
    if override:
        t.w32(override + 4, rests)
    for bone in range(count):
        for base in (rests + bone * 16, bindings + bone * 0xC0 + 0x50):
            t.floats(base, 4, -10, 10)
        if t.index % 11 == 0:
            for lane in range(4):
                t.w32(source + bone * 64 + lane * 4, rng.choice((1, 0x80000001, 0, 0x80000000)))
                t.w32(rests + bone * 16 + lane * 4, rng.choice((1, 0x80000001, 0x3F800000)))
    mode = (t.index // 6) % 6
    output = source + (-64, 0, 16, 32, 64)[mode] if mode < 5 else t.alloc(max(16, count * 64), 'snapshot')
    t.args(r3=skeleton, r4=output)
