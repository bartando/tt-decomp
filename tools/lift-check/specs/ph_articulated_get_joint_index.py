"""0x8224E668: follow instance/archetype/bound, cast and resolve, then body map.

The RTTI operation is modeled as a successful cast; the bound-index routine and
recursive counter execute their original PPC. Whole collider memory has guards;
negative indices and distinct map entries expose wrong offsets/indirections.
"""
from liftcheck.spec import *
from specs._composite_bound_inputs import tree

FUNCTION = "phArticulatedCollider_E668"
ADDRESS = 0x8224E668
SOURCE = "src/physics/bound_lookup.cpp"
TRIALS = 400


def cast(ctx):
    ctx.ret(r3=ctx.r(3))


CALLS = {
    "RTDynamicCast": model(cast),
    "rage::phBoundComposite_ResolveBoundIndex": run(),
    "rage::phBoundComposite_E750": run(),
}


def inputs(t):
    bound, total = tree(t)
    archetype = t.alloc(32, "archetype")
    instance = t.alloc(32, "instance")
    collider = t.alloc(0x280, "colliderAndGuards")
    t.w32(archetype + 12, bound)
    t.w32(instance + 4, archetype)
    t.w32(collider + 16, instance)
    for i in range(-2, 10):
        t.w32(collider + 0x204 + 4 * i, t.rng.randrange(10000))
    index = t.rng.choice((-2, -1, 0, 1, 2, 5, total - 1, total, total + 1, 0x7FFFFFFF))
    t.args(r3=collider, r4=index)
