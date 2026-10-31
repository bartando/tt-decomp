"""0x820C3870: four-byte pointer relocation, unsigned quotient and signed delta."""
from liftcheck.spec import *
FUNCTION = 'ph_AdvanceSegmentedPtr'
ADDRESS = 0x820C3870
SOURCE = 'src/physics/ph_physics.cpp'
TRIALS = 500


def inputs(t):
    descriptor = t.alloc(0x100, 'descriptorAndGuards') + 16
    arena = t.alloc(0x1000, 'resourceArena')
    start = arena + 0x400
    stride = t.pick((1, 3, 4, 7, 16, 32))
    index = t.rng.randrange(14)
    current = start + index * stride + t.rng.randrange(stride)
    t.w32(descriptor + 4, start)
    t.w32(descriptor + 0x4c, stride)
    for i in range(16):
        t.w32(descriptor + 8 + i * 4, t.pick((-0x300, -5, -1, 0, 3, 0x120)))
    slot = t.alloc(32, 'pointerAndGuards') + 12
    t.w32(slot, 0 if t.index % 4 == 0 else current)
    if t.index % 8 == 0:
        descriptor = 0
    t.args(r3=descriptor, r4=slot)
