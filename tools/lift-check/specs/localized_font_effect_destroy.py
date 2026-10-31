"""Destruction order and standalone payload ownership, running child releases.

Small acyclic trees, including two references to one child. Heap free remains
a boundary; object bytes and every recursive release/free call are compared.
"""
from liftcheck.spec import *

FUNCTION = "localizedFontEffectDestroy"
ADDRESS = 0x821512B8
SOURCE = "src/rage/localized_font_effect.cpp"
TRIALS = 400
CALLS = {0x82151268: run(), 0x820C00C0: stub(ret="void", args=("r3",))}


def inputs(t):
    rng = t.rng

    def node(depth):
        effect = t.alloc(0x24, "effect")
        for offset in (0x10, 0x14):
            t.w32(effect + offset, t.alloc(16, "payload") if rng.randrange(2) else 0)
        children = [node(depth - 1) if depth and rng.randrange(2) else 0 for _ in range(2)]
        if children[1] and rng.randrange(3) == 0:
            children[0] = children[1]
            t.w32(children[0] + 0x20, 2)
        for offset, child in zip((0x18, 0x1C), children):
            t.w32(effect + offset, child)
        t.w32(effect + 0x20, rng.choice((1, 2, 3)))
        return effect

    t.args(r3=node(2), r4=rng.getrandbits(32))
