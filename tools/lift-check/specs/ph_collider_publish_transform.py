"""0x822CB680: publish cached pose, correcting flagged bound centroid in all lanes."""
from liftcheck.spec import *
FUNCTION = 'phCollider_PublishTransform'
ADDRESS = 0x822CB680
SOURCE = 'src/physics/collider_velocity.cpp'
TRIALS = 500
FTOL = 1e-99
FP_CONTRACT = 'off'


def inputs(t):
    obj = t.alloc(0x220, 'colliderAndGuards') + 16
    t.floats(obj + 0xa0, 16, -20, 20)
    instance = t.alloc(0x70, 'instanceAndGuards') + 16
    archetype = t.alloc(32, 'archetype')
    bound = t.alloc(0x80, 'boundAndGuards') + 16
    t.floats(bound + 0x50, 4, -20, 20)
    t.w8(bound + 6, t.pick((0, 1, 2, 0x80, 0xff)))
    if t.index % 4 == 0:
        t.w32(bound + 0x50 + 4 * t.rng.randrange(4), t.pick((1, 0x807fffff,
              0x7f800000, 0xff800000, 0x7fc00000, 0x80000000)))
    if t.index % 3 == 0:
        # Output overlaps cached matrix or centroid; all loads precede stores.
        instance = obj + t.pick((0x90, 0xa0, 0xb0))
    elif t.index % 5 == 0:
        instance = bound + 0x20
    t.w32(obj + 0x10, instance)
    t.w32(instance + 4, archetype)
    t.w32(archetype + 0xc, bound)
    t.args(r3=obj)
